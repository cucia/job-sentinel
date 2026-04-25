import argparse
import hashlib
import os
import re
import time
from datetime import datetime, timezone

from src.ai.scorer import evaluate_job
from src.ai.agents_wrapper import evaluate_job_with_agents
from src.core.config import load_profile, load_settings
from src.core.limiter import can_apply
from src.core.logger import log
from src.core.platform_registry import get_enrichers, get_platforms
from src.core.policy import policy_allows
from src.core.storage import (
    get_job,
    get_model_state,
    init_db,
    has_seen_job,
    enqueue_job,
    next_queued_job,
    prune_jobs,
    record_decision,
    upsert_job,
    update_job,
)
from src.platforms.linkedin.collector import collect_jobs as collect_linkedin
from src.platforms.linkedin.url_utils import normalize_job_url as normalize_linkedin_job_url
from src.platforms.indeed.collector import collect_jobs as collect_indeed
from src.platforms.naukri.collector import collect_jobs as collect_naukri


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve_db_path(base_dir: str, settings: dict) -> str:
    db_path = settings.get("storage", {}).get("db_path", "data/jobsentinel.db")
    if os.path.isabs(db_path):
        return db_path
    return os.path.join(base_dir, db_path)


def _make_job_key(job: dict) -> str:
    job_url = (job.get("job_url") or "").strip()
    if (job.get("platform") or "").strip().lower() == "linkedin":
        job_url = normalize_linkedin_job_url(job_url)
    if job_url:
        raw = f"{job.get('platform')}|{job_url}"
    else:
        raw = f"{job.get('platform')}|{job.get('title')}|{job.get('company')}|{job.get('location')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _is_entry_level(job: dict, blocklist: list[str]) -> bool:
    text = f"{job.get('title') or ''} {job.get('description') or ''}".lower()
    return not any(term in text for term in blocklist)


def _parse_posted_at(value: str | None) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _relative_posted_minutes(value: str | None) -> int | None:
    text = (value or "").strip().lower()
    if not text:
        return None
    if any(token in text for token in ("just now", "today", "few moments")):
        return 0
    match = re.search(
        r"(\d+)\s*(min|mins|minute|minutes|hr|hrs|hour|hours|day|days|week|weeks|month|months)",
        text,
    )
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    unit_minutes = {
        "min": 1,
        "mins": 1,
        "minute": 1,
        "minutes": 1,
        "hr": 60,
        "hrs": 60,
        "hour": 60,
        "hours": 60,
        "day": 1440,
        "days": 1440,
        "week": 10080,
        "weeks": 10080,
        "month": 43200,
        "months": 43200,
    }
    return amount * unit_minutes[unit]


def _job_sort_key(indexed_job: tuple[int, dict]) -> tuple[int, float, int]:
    index, job = indexed_job
    posted_at = _parse_posted_at(job.get("posted_at"))
    if posted_at:
        return (3, posted_at.timestamp(), -index)
    relative_minutes = _relative_posted_minutes(job.get("posted_text"))
    if relative_minutes is not None:
        return (2, float(-relative_minutes), -index)
    return (1, 0.0, -index)


def _select_latest_jobs(jobs: list[dict], limit: int) -> list[dict]:
    if limit <= 0:
        return []
    deduped: list[dict] = []
    seen_job_keys: set[str] = set()
    for job in jobs:
        current = dict(job)
        current["job_key"] = _make_job_key(current)
        if current["job_key"] in seen_job_keys:
            continue
        seen_job_keys.add(current["job_key"])
        deduped.append(current)
    ranked = sorted(enumerate(deduped), key=_job_sort_key, reverse=True)
    return [job for _idx, job in ranked[:limit]]


def _merge_existing_job(job: dict, existing_job: dict | None) -> dict:
    if not existing_job:
        return job
    merged = dict(job)
    for field in ("title", "company", "location", "description", "job_url", "posted_at", "posted_text", "easy_apply"):
        value = merged.get(field)
        if isinstance(value, str):
            missing = not value.strip()
        else:
            missing = value in (None, "")
        if missing:
            replacement = existing_job.get(field)
            merged[field] = replacement if replacement is not None else ""
    return merged


def _rank_apply_candidates(candidates: list[dict], easy_apply_first: bool) -> list[dict]:
    def _candidate_key(candidate: dict) -> tuple[int, float, int, float, int]:
        job = candidate["job"]
        index = int(candidate.get("index", 0) or 0)
        recency_key = _job_sort_key((index, job))
        easy_apply_rank = 1 if easy_apply_first and int(job.get("easy_apply") or 0) == 1 else 0
        priority_score = float(candidate.get("priority_score") or candidate.get("score") or 0)
        return (easy_apply_rank, priority_score, recency_key[0], recency_key[1], recency_key[2])

    return sorted(candidates, key=_candidate_key, reverse=True)


def collect_jobs(settings: dict, profile: dict, enabled_override: list[str] | None = None) -> list:
    enabled = enabled_override or settings.get("platforms", {}).get("enabled", [])
    jobs = []

    if "linkedin" in enabled:
        try:
            linkedin_jobs = collect_linkedin(settings, profile)
            log(f"LinkedIn: collector returned {len(linkedin_jobs)} jobs")
            jobs.extend(linkedin_jobs)
        except Exception as exc:
            log(f"LinkedIn collection failed: {exc}")

    if "indeed" in enabled:
        try:
            indeed_jobs = collect_indeed(settings, profile)
            log(f"Indeed: collector returned {len(indeed_jobs)} jobs")
            jobs.extend(indeed_jobs)
        except Exception as exc:
            log(f"Indeed collection failed: {exc}")

    if "naukri" in enabled:
        try:
            naukri_jobs = collect_naukri(settings, profile)
            log(f"Naukri: collector returned {len(naukri_jobs)} jobs")
            jobs.extend(naukri_jobs)
        except Exception as exc:
            log(f"Naukri collection failed: {exc}")

    log(f"Collectors total: {len(jobs)} jobs across enabled platforms")
    return jobs


def _run_queue_cycle(
    base_dir: str,
    settings: dict,
    profile: dict,
    db_path: str,
    model_state: dict,
    platforms: dict,
    enrichers: dict,
    enabled_override: list[str] | None = None,
) -> None:
    jobs = collect_jobs(settings, profile, enabled_override)
    log(f"Collected {len(jobs)} jobs")
    daily_limit = settings.get("limits", {}).get("daily_applications", 10)
    policy = settings.get("policy", {})
    resume_path = settings.get("app", {}).get("resume_path", "resumes/resume.pdf")
    apply_all = settings.get("app", {}).get("apply_all", False)
    use_ai = settings.get("app", {}).get("use_ai", False)
    use_llm = settings.get("ai", {}).get("use_llm", False)
    llm_model = settings.get("ai", {}).get("llm_model", "llama3.2:latest")
    use_policy = settings.get("app", {}).get("use_policy", False)
    enrich_before_ai = settings.get("app", {}).get("enrich_before_ai", True)
    entry_level_only = settings.get("app", {}).get("entry_level_only", True)
    seniority_blocklist = settings.get("app", {}).get(
        "seniority_blocklist",
        ["senior", "lead", "manager", "principal", "director", "head", "staff", "architect"],
    )
    if not os.path.isabs(resume_path):
        resume_path = os.path.join(base_dir, resume_path)
    log(
        "Cycle config: "
        f"apply_all={apply_all} use_ai={use_ai} use_llm={use_llm} llm_model={llm_model} use_policy={use_policy} "
        f"enrich_before_ai={enrich_before_ai} entry_level_only={entry_level_only} "
        f"daily_limit={daily_limit}"
    )

    # Phase 1: collect + enqueue
    seen_count = 0
    enqueued_count = 0
    entry_skipped_count = 0
    policy_skipped_count = 0
    ai_skipped_count = 0
    review_count = 0
    for job in jobs:
        job["job_key"] = _make_job_key(job)
        if has_seen_job(db_path, job["job_key"]):
            seen_count += 1
            continue
        enqueue_job(db_path, job)
        enqueued_count += 1

        platform = job.get("platform")
        enricher = enrichers.get(platform)
        if use_ai and enrich_before_ai and enricher and not (job.get("description") or "").strip():
            try:
                enrich_fields = enricher(job, settings) or {}
                if enrich_fields:
                    job.update({k: v for k, v in enrich_fields.items() if v})
                    update_job(
                        db_path,
                        job["job_key"],
                        description=job.get("description", ""),
                        company=job.get("company", ""),
                        location=job.get("location", ""),
                    )
                    log(
                        "Enriched job: "
                        f"platform={platform} description_len={len(job.get('description') or '')}"
                    )
            except Exception as exc:
                log(f"Enricher failed for {platform}: {exc}")

        if entry_level_only and not _is_entry_level(job, seniority_blocklist):
            update_job(db_path, job["job_key"], status="skipped")
            record_decision(db_path, job["job_key"], "seniority_reject", 0)
            entry_skipped_count += 1
            continue

        if use_policy and not policy_allows(job, policy):
            update_job(db_path, job["job_key"], status="skipped")
            record_decision(db_path, job["job_key"], "policy_reject", 0)
            policy_skipped_count += 1
            continue

        if use_ai:
            use_agents = settings.get("ai", {}).get("use_agents", False)
            if use_agents:
                decision = evaluate_job_with_agents(job, profile, settings)
            else:
                min_score = settings.get("ai", {}).get("min_score", 70)
                uncertainty_margin = settings.get("ai", {}).get("uncertainty_margin", 5)
                decision = evaluate_job(job, profile, min_score, uncertainty_margin, model_state=model_state, use_llm=use_llm, llm_model=llm_model)
            if not decision["apply"] and not decision["confused"]:
                update_job(db_path, job["job_key"], status="skipped")
                record_decision(db_path, job["job_key"], "ai_reject", decision["score"])
                log(
                    "AI rejected: "
                    f"title={job.get('title')} score={decision['score']} "
                    f"heuristic={decision['heuristic_score']} learned={decision['learned_adjustment']} "
                    f"terms={decision['matched_terms']}"
                )
                ai_skipped_count += 1
                continue
            if decision["confused"]:
                update_job(db_path, job["job_key"], status="review")
                record_decision(db_path, job["job_key"], "ai_review", decision["score"])
                log(
                    "AI review: "
                    f"title={job.get('title')} score={decision['score']} "
                    f"heuristic={decision['heuristic_score']} learned={decision['learned_adjustment']} "
                    f"terms={decision['matched_terms']}"
                )
                review_count += 1
                continue
            record_decision(db_path, job["job_key"], "ai_accept", decision["score"])
            log(
                "AI accepted: "
                f"title={job.get('title')} score={decision['score']} "
                f"heuristic={decision['heuristic_score']} learned={decision['learned_adjustment']} "
                f"terms={decision['matched_terms']} trained_examples={decision['trained_examples']}"
            )

    log(
        "Phase 1 summary: "
        f"seen={seen_count} enqueued={enqueued_count} "
        f"entry_skipped={entry_skipped_count} policy_skipped={policy_skipped_count} "
        f"ai_skipped={ai_skipped_count} review={review_count}"
    )

    # Phase 2: apply jobs from the queue
    applied_count = 0
    review_apply_count = 0
    skipped_apply_count = 0
    deferred_apply_count = 0
    while apply_all or can_apply(db_path, daily_limit):
        job = next_queued_job(db_path)
        if not job:
            break
        platform = job.get("platform")
        apply_fn = platforms.get(platform)
        if not apply_fn:
            update_job(db_path, job["job_key"], status="skipped")
            skipped_apply_count += 1
            continue
        log(
            "Applying: "
            f"platform={platform} title={job.get('title')} url={job.get('job_url')}"
        )
        try:
            result = apply_fn(job, resume_path, settings)
            status = None
            easy_apply = None
            if isinstance(result, tuple):
                status, easy_apply = result
            if status == "applied":
                update_job(db_path, job["job_key"], status="applied", easy_apply=easy_apply)
                applied_count += 1
                log(f"Apply result: status=applied easy_apply={easy_apply}")
            elif status == "review":
                update_job(db_path, job["job_key"], status="review", easy_apply=easy_apply)
                review_apply_count += 1
                log(f"Apply result: status=review easy_apply={easy_apply}")
            elif status == "skipped":
                update_job(db_path, job["job_key"], status="skipped", easy_apply=easy_apply)
                skipped_apply_count += 1
                log(f"Apply result: status=skipped easy_apply={easy_apply}")
            else:
                update_job(db_path, job["job_key"], status="deferred", easy_apply=easy_apply)
                deferred_apply_count += 1
                log(f"Apply result: status=deferred easy_apply={easy_apply}")
        except Exception as exc:
            log(f"Apply failed for {job.get('job_key')}: {exc}")
            update_job(db_path, job["job_key"], status="review", easy_apply=0)
            review_apply_count += 1

    log(
        "Phase 2 summary: "
        f"applied={applied_count} review={review_apply_count} "
        f"skipped={skipped_apply_count} deferred={deferred_apply_count}"
    )


def _run_direct_latest_cycle(
    base_dir: str,
    settings: dict,
    profile: dict,
    db_path: str,
    model_state: dict,
    platforms: dict,
    enrichers: dict,
    enabled_override: list[str] | None = None,
) -> None:
    collected_jobs = collect_jobs(settings, profile, enabled_override)
    latest_results_limit = int(settings.get("app", {}).get("latest_results_limit", 100))
    history_limit = int(settings.get("storage", {}).get("history_limit", 400))
    jobs = _select_latest_jobs(collected_jobs, latest_results_limit)

    daily_limit = settings.get("limits", {}).get("daily_applications", 10)
    policy = settings.get("policy", {})
    resume_path = settings.get("app", {}).get("resume_path", "resumes/resume.pdf")
    apply_all = settings.get("app", {}).get("apply_all", False)
    use_ai = settings.get("app", {}).get("use_ai", False)
    use_llm = settings.get("ai", {}).get("use_llm", False)
    llm_model = settings.get("ai", {}).get("llm_model", "llama3.2:latest")
    use_policy = settings.get("app", {}).get("use_policy", False)
    enrich_before_ai = settings.get("app", {}).get("enrich_before_ai", True)
    easy_apply_first = settings.get("app", {}).get("easy_apply_first", True)
    entry_level_only = settings.get("app", {}).get("entry_level_only", True)
    seniority_blocklist = settings.get("app", {}).get(
        "seniority_blocklist",
        ["senior", "lead", "manager", "principal", "director", "head", "staff", "architect"],
    )
    if not os.path.isabs(resume_path):
        resume_path = os.path.join(base_dir, resume_path)

    log(
        "Direct cycle config: "
        f"latest_results_limit={latest_results_limit} history_limit={history_limit} "
        f"apply_all={apply_all} use_ai={use_ai} use_llm={use_llm} llm_model={llm_model} use_policy={use_policy} "
        f"enrich_before_ai={enrich_before_ai} easy_apply_first={easy_apply_first} "
        f"entry_level_only={entry_level_only} "
        f"daily_limit={daily_limit}"
    )
    log(
        "Direct cycle batch: "
        f"collected={len(collected_jobs)} selected={len(jobs)}"
    )

    counts = {
        "tracked": 0,
        "entry_skipped": 0,
        "policy_skipped": 0,
        "ai_skipped": 0,
        "ranked": 0,
        "easy_apply_candidates": 0,
        "review": 0,
        "applied": 0,
        "skipped": 0,
        "deferred": 0,
    }
    apply_candidates: list[dict] = []

    for job in jobs:
        existing_job = get_job(db_path, job["job_key"])
        job = _merge_existing_job(job, existing_job)
        existing_status = (existing_job or {}).get("status")
        if existing_status in {"applied", "rejected", "skipped", "review"}:
            upsert_job(
                db_path,
                job,
                status=existing_status,
                easy_apply=(existing_job or {}).get("easy_apply"),
                score=(existing_job or {}).get("score"),
                decision=(existing_job or {}).get("decision"),
            )
            counts["tracked"] += 1
            continue

        platform = job.get("platform")
        enricher = enrichers.get(platform)
        if use_ai and enrich_before_ai and enricher and not (job.get("description") or "").strip():
            try:
                enrich_fields = enricher(job, settings) or {}
                if enrich_fields:
                    job.update({k: v for k, v in enrich_fields.items() if v})
                    log(
                        "Enriched direct job: "
                        f"platform={platform} description_len={len(job.get('description') or '')}"
                    )
            except Exception as exc:
                log(f"Enricher failed for {platform}: {exc}")

        if entry_level_only and not _is_entry_level(job, seniority_blocklist):
            upsert_job(db_path, job, status="skipped", score=0, decision="seniority_reject")
            counts["entry_skipped"] += 1
            continue

        if use_policy and not policy_allows(job, policy):
            upsert_job(db_path, job, status="skipped", score=0, decision="policy_reject")
            counts["policy_skipped"] += 1
            continue

        decision = None
        score = None
        priority_score = 0.0
        if use_ai:
            use_agents = settings.get("ai", {}).get("use_agents", False)
            if use_agents:
                decision = evaluate_job_with_agents(job, profile, settings)
            else:
                min_score = settings.get("ai", {}).get("min_score", 70)
                uncertainty_margin = settings.get("ai", {}).get("uncertainty_margin", 5)
                decision = evaluate_job(job, profile, min_score, uncertainty_margin, model_state=model_state, use_llm=use_llm, llm_model=llm_model)
            score = decision["score"]
            priority_score = float(decision.get("priority_score") or score or 0)
            if not decision["apply"] and not decision["confused"]:
                upsert_job(db_path, job, status="skipped", score=score, decision="ai_reject")
                log(
                    "AI rejected: "
                    f"title={job.get('title')} score={decision['score']} "
                    f"heuristic={decision['heuristic_score']} learned={decision['learned_adjustment']} "
                    f"terms={decision['matched_terms']} signals={decision.get('signals', [])}"
                )
                counts["ai_skipped"] += 1
                continue
            if decision["confused"]:
                upsert_job(db_path, job, status="review", score=score, decision="ai_review")
                log(
                    "AI review: "
                    f"title={job.get('title')} score={decision['score']} "
                    f"heuristic={decision['heuristic_score']} learned={decision['learned_adjustment']} "
                    f"terms={decision['matched_terms']} signals={decision.get('signals', [])}"
                )
                counts["review"] += 1
                continue
            log(
                "AI accepted: "
                f"title={job.get('title')} score={decision['score']} "
                f"priority={decision.get('priority_score')} easy_apply={job.get('easy_apply', 0)} "
                f"heuristic={decision['heuristic_score']} learned={decision['learned_adjustment']} "
                f"terms={decision['matched_terms']} signals={decision.get('signals', [])} "
                f"trained_examples={decision['trained_examples']}"
            )
        else:
            score = int(job.get("score") or 0)
            priority_score = float(score)

        if not apply_all:
            upsert_job(
                db_path,
                job,
                status="deferred",
                score=score,
                decision="accepted_pending_apply" if use_ai else "collected_pending_apply",
            )
            counts["deferred"] += 1
            continue

        apply_candidates.append(
            {
                "index": len(apply_candidates),
                "job": job,
                "score": score,
                "priority_score": priority_score,
                "signals": (decision or {}).get("signals", []),
            }
        )
        counts["ranked"] += 1
        counts["easy_apply_candidates"] += int(job.get("easy_apply") or 0)

    ranked_candidates = _rank_apply_candidates(apply_candidates, bool(easy_apply_first))
    if ranked_candidates:
        preview = ", ".join(
            (
                f"{candidate['job'].get('platform')}::{candidate['job'].get('title')} "
                f"[score={candidate.get('score')} priority={candidate.get('priority_score')} "
                f"easy={candidate['job'].get('easy_apply', 0)}]"
            )
            for candidate in ranked_candidates[:5]
        )
        log(f"Direct ranking top candidates: {preview}")

    for candidate in ranked_candidates:
        job = candidate["job"]
        score = candidate.get("score")
        priority_score = candidate.get("priority_score")
        platform = job.get("platform")

        if not can_apply(db_path, daily_limit):
            upsert_job(db_path, job, status="deferred", score=score, decision="daily_limit_deferred")
            counts["deferred"] += 1
            continue

        apply_fn = platforms.get(platform)
        if not apply_fn:
            upsert_job(db_path, job, status="skipped", score=score, decision="no_apply_module")
            counts["skipped"] += 1
            continue

        log(
            "Direct applying: "
            f"platform={platform} title={job.get('title')} url={job.get('job_url')} "
            f"score={score} priority={priority_score} easy_apply={job.get('easy_apply', 0)} "
            f"signals={candidate.get('signals', [])}"
        )
        try:
            result = apply_fn(job, resume_path, settings)
            result_status = None
            easy_apply = job.get("easy_apply")
            if isinstance(result, tuple):
                result_status, easy_apply = result

            if result_status == "applied":
                upsert_job(db_path, job, status="applied", easy_apply=easy_apply, score=score, decision="applied_direct")
                counts["applied"] += 1
                log(f"Direct apply result: status=applied easy_apply={easy_apply}")
            elif result_status == "review":
                upsert_job(db_path, job, status="review", easy_apply=easy_apply, score=score, decision="apply_review")
                counts["review"] += 1
                log(f"Direct apply result: status=review easy_apply={easy_apply}")
            elif result_status == "skipped":
                upsert_job(db_path, job, status="skipped", easy_apply=easy_apply, score=score, decision="apply_skipped")
                counts["skipped"] += 1
                log(f"Direct apply result: status=skipped easy_apply={easy_apply}")
            else:
                upsert_job(db_path, job, status="deferred", easy_apply=easy_apply, score=score, decision="apply_deferred")
                counts["deferred"] += 1
                log(f"Direct apply result: status=deferred easy_apply={easy_apply}")
        except Exception as exc:
            log(f"Direct apply failed for {job.get('job_key')}: {exc}")
            upsert_job(
                db_path,
                job,
                status="review",
                easy_apply=job.get("easy_apply"),
                score=score,
                decision="apply_failed",
            )
            counts["review"] += 1

    prune_jobs(db_path, history_limit)
    log(
        "Direct cycle summary: "
        f"tracked={counts['tracked']} entry_skipped={counts['entry_skipped']} "
        f"policy_skipped={counts['policy_skipped']} ai_skipped={counts['ai_skipped']} "
        f"ranked={counts['ranked']} easy_apply_candidates={counts['easy_apply_candidates']} "
        f"applied={counts['applied']} review={counts['review']} "
        f"skipped={counts['skipped']} deferred={counts['deferred']}"
    )


def run_cycle(enabled_override: list[str] | None = None) -> None:
    base_dir = _base_dir()
    settings = load_settings(base_dir)
    profile = load_profile(base_dir)
    platforms = get_platforms()
    enrichers = get_enrichers()

    db_path = _resolve_db_path(base_dir, settings)
    init_db(db_path)
    model_state = get_model_state(db_path)

    pipeline_mode = (settings.get("app", {}).get("pipeline_mode") or "direct_latest").strip().lower()
    if pipeline_mode == "direct_latest":
        _run_direct_latest_cycle(
            base_dir,
            settings,
            profile,
            db_path,
            model_state,
            platforms,
            enrichers,
            enabled_override,
        )
        return

    _run_queue_cycle(
        base_dir,
        settings,
        profile,
        db_path,
        model_state,
        platforms,
        enrichers,
        enabled_override,
    )


def main() -> None:
    log("JobSentinel started")
    settings = load_settings(_base_dir())
    interval = settings.get("app", {}).get("run_interval_seconds", 300)
    env_platforms = os.environ.get("JOBSENTINEL_PLATFORMS", "").strip()

    parser = argparse.ArgumentParser(description="JobSentinel runner")
    parser.add_argument(
        "--platforms",
        help="Comma-separated list of platforms to run (e.g., linkedin,naukri).",
        default="",
    )
    args, _unknown = parser.parse_known_args()
    platforms_arg = args.platforms.strip()
    platforms_override = []
    source = ""
    if platforms_arg:
        platforms_override = [p.strip() for p in platforms_arg.split(",") if p.strip()]
        source = "args"
    elif env_platforms:
        platforms_override = [p.strip() for p in env_platforms.split(",") if p.strip()]
        source = "env"
    if platforms_override:
        log(f"Platform override ({source}): {platforms_override}")

    while True:
        run_cycle(platforms_override or None)
        time.sleep(interval)


if __name__ == "__main__":
    main()

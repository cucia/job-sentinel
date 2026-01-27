import hashlib
import os
import time

from core.ai_engine import evaluate_job
from core.config import load_profile, load_settings
from core.limiter import can_apply
from core.logger import log
from core.platform_registry import get_enrichers, get_platforms
from core.policy import policy_allows
from core.storage import (
    init_db,
    has_seen_job,
    enqueue_job,
    next_queued_job,
    record_decision,
    update_job,
)
from platforms.linkedin.collector import collect_jobs as collect_linkedin
from platforms.naukri.collector import collect_jobs as collect_naukri


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _resolve_db_path(base_dir: str, settings: dict) -> str:
    db_path = settings.get("storage", {}).get("db_path", "data/jobsentinel.db")
    if os.path.isabs(db_path):
        return db_path
    return os.path.join(base_dir, db_path)


def _make_job_key(job: dict) -> str:
    job_url = (job.get("job_url") or "").strip()
    if job_url:
        raw = f"{job.get('platform')}|{job_url}"
    else:
        raw = f"{job.get('platform')}|{job.get('title')}|{job.get('company')}|{job.get('location')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _is_entry_level(job: dict, blocklist: list[str]) -> bool:
    text = f"{job.get('title') or ''} {job.get('description') or ''}".lower()
    return not any(term in text for term in blocklist)


def collect_jobs(settings: dict, profile: dict) -> list:
    enabled = settings.get("platforms", {}).get("enabled", [])
    jobs = []

    if "linkedin" in enabled:
        try:
            linkedin_jobs = collect_linkedin(settings, profile)
            log(f"LinkedIn: collector returned {len(linkedin_jobs)} jobs")
            jobs.extend(linkedin_jobs)
        except Exception as exc:
            log(f"LinkedIn collection failed: {exc}")

    if "naukri" in enabled:
        try:
            naukri_jobs = collect_naukri(settings, profile)
            log(f"Naukri: collector returned {len(naukri_jobs)} jobs")
            jobs.extend(naukri_jobs)
        except Exception as exc:
            log(f"Naukri collection failed: {exc}")

    log(f"Collectors total: {len(jobs)} jobs across enabled platforms")
    return jobs


def run_cycle() -> None:
    base_dir = _base_dir()
    settings = load_settings(base_dir)
    profile = load_profile(base_dir)
    platforms = get_platforms()
    enrichers = get_enrichers()

    db_path = _resolve_db_path(base_dir, settings)
    init_db(db_path)

    jobs = collect_jobs(settings, profile)
    log(f"Collected {len(jobs)} jobs")
    daily_limit = settings.get("limits", {}).get("daily_applications", 10)
    policy = settings.get("policy", {})
    resume_path = settings.get("app", {}).get("resume_path", "resumes/resume.pdf")
    apply_all = settings.get("app", {}).get("apply_all", False)
    use_ai = settings.get("app", {}).get("use_ai", False)
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
        f"apply_all={apply_all} use_ai={use_ai} use_policy={use_policy} "
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
            min_score = settings.get("ai", {}).get("min_score", 70)
            uncertainty_margin = settings.get("ai", {}).get("uncertainty_margin", 5)
            decision = evaluate_job(job, profile, min_score, uncertainty_margin)
            if not decision["apply"] and not decision["confused"]:
                update_job(db_path, job["job_key"], status="skipped")
                record_decision(db_path, job["job_key"], "ai_decision", decision["score"])
                ai_skipped_count += 1
                continue
            if decision["confused"]:
                update_job(db_path, job["job_key"], status="review")
                record_decision(db_path, job["job_key"], "ai_decision", decision["score"])
                review_count += 1
                continue
            record_decision(db_path, job["job_key"], "ai_decision", decision["score"])

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


def main() -> None:
    log("JobSentinel started")
    settings = load_settings(_base_dir())
    interval = settings.get("app", {}).get("run_interval_seconds", 300)

    while True:
        run_cycle()
        time.sleep(interval)


if __name__ == "__main__":
    main()

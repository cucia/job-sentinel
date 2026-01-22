import hashlib
import os
import time

from core.ai_engine import evaluate_job
from core.config import load_profile, load_settings
from core.limiter import can_apply
from core.logger import log
from core.platform_registry import get_platforms
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
    raw = f"{job.get('platform')}|{job.get('title')}|{job.get('company')}|{job.get('location')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def collect_jobs(settings: dict, profile: dict) -> list:
    enabled = settings.get("platforms", {}).get("enabled", [])
    jobs = []

    if "linkedin" in enabled:
        try:
            jobs.extend(collect_linkedin(settings, profile))
        except Exception as exc:
            log(f"LinkedIn collection failed: {exc}")

    if "naukri" in enabled:
        try:
            jobs.extend(collect_naukri(settings, profile))
        except Exception as exc:
            log(f"Naukri collection failed: {exc}")

    return jobs


def run_cycle() -> None:
    base_dir = _base_dir()
    settings = load_settings(base_dir)
    profile = load_profile(base_dir)
    platforms = get_platforms()

    db_path = _resolve_db_path(base_dir, settings)
    init_db(db_path)

    for job in collect_jobs(settings, profile):
        job["job_key"] = _make_job_key(job)
        if not has_seen_job(db_path, job["job_key"]):
            enqueue_job(db_path, job)

    daily_limit = settings.get("limits", {}).get("daily_applications", 10)
    min_score = settings.get("ai", {}).get("min_score", 70)
    uncertainty_margin = settings.get("ai", {}).get("uncertainty_margin", 5)
    policy = settings.get("policy", {})

    while True:
        job = next_queued_job(db_path)
        if not job:
            break

        if not policy_allows(job, policy):
            record_decision(db_path, job["job_key"], "policy_reject", 0)
            update_job(db_path, job["job_key"], status="rejected")
            continue

        decision = evaluate_job(job, profile, min_score, uncertainty_margin)
        record_decision(db_path, job["job_key"], "ai_decision", decision["score"])

        if not decision["apply"]:
            update_job(db_path, job["job_key"], status="rejected")
            continue

        if decision.get("confused"):
            update_job(db_path, job["job_key"], status="review")
            continue

        if not can_apply(db_path, daily_limit):
            update_job(db_path, job["job_key"], status="deferred")
            break

        platform = job.get("platform")
        apply_fn = platforms.get(platform)
        if not apply_fn:
            update_job(db_path, job["job_key"], status="skipped")
            continue

        resume_path = settings.get("app", {}).get("resume_path", "resumes/resume.pdf")
        if not os.path.isabs(resume_path):
            resume_path = os.path.join(base_dir, resume_path)

        apply_fn(job, resume_path, settings)
        update_job(db_path, job["job_key"], status="applied")


def main() -> None:
    log("JobSentinel started")
    settings = load_settings(_base_dir())
    interval = settings.get("app", {}).get("run_interval_seconds", 300)

    while True:
        run_cycle()
        time.sleep(interval)


if __name__ == "__main__":
    main()

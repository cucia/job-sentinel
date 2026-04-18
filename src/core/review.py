import argparse
import os

from src.ai.scorer import update_model
from src.core.config import load_profile, load_settings
from src.core.storage import (
    get_feedback_label,
    get_job,
    get_model_state,
    init_db,
    list_jobs,
    record_feedback,
    save_model_state,
    update_job,
)


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve_db_path(base_dir: str, settings: dict) -> str:
    db_path = settings.get("storage", {}).get("db_path", "data/jobsentinel.db")
    if os.path.isabs(db_path):
        return db_path
    return os.path.join(base_dir, db_path)


def _print_jobs(jobs: list[dict]) -> None:
    if not jobs:
        print("No jobs found.")
        return

    for job in jobs:
        posted = job.get("posted_at") or job.get("posted_text") or job.get("created_at") or "-"
        print(
            f"{job['job_key']} | {job['status']} | {job['platform']} | "
            f"{job['title']} | {job.get('company') or '-'} | {posted}"
        )


def _inverse_feedback_label(label: str | None) -> str | None:
    normalized = (label or "").strip().lower()
    if normalized in {"approved", "applied", "positive"}:
        return "rejected"
    if normalized in {"rejected", "negative", "skipped"}:
        return "approved"
    return None


def _apply_feedback_learning(base_dir: str, db_path: str, job_key: str, label: str) -> None:
    previous_label = get_feedback_label(db_path, job_key)
    record_feedback(db_path, job_key, label, source="review-cli")
    if previous_label == label:
        return
    job = get_job(db_path, job_key)
    if not job:
        return
    profile = load_profile(base_dir)
    updated_state = get_model_state(db_path)
    undo_label = _inverse_feedback_label(previous_label)
    if undo_label:
        updated_state = update_model(job, profile, undo_label, updated_state)
    updated_state = update_model(job, profile, label, updated_state)
    save_model_state(
        db_path,
        updated_state.get("weights", {}),
        float(updated_state.get("bias", 0.0) or 0.0),
        int(updated_state.get("trained_examples", 0) or 0),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Review queued and review jobs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List jobs by status.")
    list_parser.add_argument(
        "status",
        nargs="?",
        default="review",
        choices=["all", "applied", "queued", "review", "rejected", "skipped", "deferred"],
    )
    list_parser.add_argument("--platform", choices=["linkedin", "indeed", "naukri"])
    list_parser.add_argument("--limit", type=int, default=20)

    approve_parser = subparsers.add_parser("approve", help="Approve a job back into the queue.")
    approve_parser.add_argument("job_key")

    reject_parser = subparsers.add_parser("reject", help="Reject a job.")
    reject_parser.add_argument("job_key")

    applied_parser = subparsers.add_parser("mark-applied", help="Mark a job as applied.")
    applied_parser.add_argument("job_key")

    args = parser.parse_args()

    base_dir = _base_dir()
    settings = load_settings(base_dir)
    db_path = _resolve_db_path(base_dir, settings)
    init_db(db_path)

    if args.command == "list":
        statuses = None if args.status == "all" else [args.status]
        jobs = list_jobs(db_path, statuses=statuses, platform=args.platform, limit=args.limit)
        _print_jobs(jobs)
        return

    next_status = {
        "approve": "queued",
        "reject": "rejected",
        "mark-applied": "applied",
    }[args.command]
    feedback_label = {
        "approve": "approved",
        "reject": "rejected",
        "mark-applied": "applied",
    }[args.command]
    _apply_feedback_learning(base_dir, db_path, args.job_key, feedback_label)
    update_job(db_path, args.job_key, status=next_status)
    print(f"Updated {args.job_key} -> {next_status}")


if __name__ == "__main__":
    main()

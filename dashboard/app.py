import csv
import io
import os
import sqlite3
import time
from datetime import datetime, timezone

import docker
from flask import Flask, request, redirect, url_for, render_template, Response

from agents.assistant import handle_chat, _load_recent_log
from agents.profile_store import load_profile
from core.config import load_settings, save_settings
from core.storage import init_db, list_jobs, update_job

app = Flask(__name__)
START_TIME = time.time()


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _resolve_db_path(base_dir: str, settings: dict) -> str:
    db_path = settings.get("storage", {}).get("db_path", "data/jobsentinel.db")
    if os.path.isabs(db_path):
        return db_path
    return os.path.join(base_dir, db_path)


def _load_settings_and_db() -> tuple[str, dict, str]:
    base_dir = _base_dir()
    settings = load_settings(base_dir)
    db_path = _resolve_db_path(base_dir, settings)
    init_db(db_path)
    return base_dir, settings, db_path


def _docker_client():
    try:
        return docker.from_env()
    except Exception:
        return None


def _service_container_status(service: str) -> str:
    client = _docker_client()
    if not client:
        return "unknown"
    try:
        containers = client.containers.list(all=True, filters={"label": f"com.docker.compose.service={service}"})
        if not containers:
            return "not-found"
        return containers[0].status
    except Exception:
        return "unknown"


def _service_status_label(status: str) -> str:
    status_l = (status or "").lower()
    if status_l in {"running", "healthy"}:
        return "live"
    if status_l in {"paused"}:
        return "paused"
    if status_l in {"exited", "dead", "created"}:
        return "stopped"
    if status_l in {"restarting"}:
        return "paused"
    return "unknown"


def _human_duration(seconds: float) -> str:
    seconds = int(max(seconds, 0))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days}d {hours:02d}h {minutes:02d}m"
    if hours > 0:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m {sec:02d}s"


def _job_stats(db_path: str) -> dict:
    stats: dict[str, int] = {
        "total": 0,
        "queued": 0,
        "review": 0,
        "applied": 0,
        "rejected": 0,
        "skipped": 0,
        "deferred": 0,
    }
    last_updated = None
    applied_today = 0

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT status, COUNT(1) FROM jobs GROUP BY status")
        for status, count in cur.fetchall():
            if status in stats:
                stats[status] = int(count)
            else:
                stats[status] = int(count)
        stats["total"] = sum(v for k, v in stats.items() if k != "total")

        row = conn.execute("SELECT MAX(updated_at) FROM jobs").fetchone()
        if row:
            last_updated = row[0]

        today = datetime.now(timezone.utc).date().isoformat()
        row = conn.execute(
            """
            SELECT COUNT(1)
            FROM jobs
            WHERE status = 'applied'
              AND substr(applied_at, 1, 10) = ?
            """,
            (today,),
        ).fetchone()
        if row and row[0] is not None:
            applied_today = int(row[0])

    return {
        "counts": stats,
        "last_updated": last_updated,
        "applied_today": applied_today,
    }


def _health_info(base_dir: str, db_path: str, settings: dict) -> dict:
    db_size = 0
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)
    sessions_cfg = settings.get("platforms", {}).get("sessions", {})
    session_info = {}
    for platform in ("linkedin", "indeed", "naukri"):
        path = sessions_cfg.get(platform, f"sessions/{platform}.json")
        if not os.path.isabs(path):
            path = os.path.join(base_dir, path)
        session_info[platform] = {
            "path": path,
            "exists": os.path.exists(path),
            "size": os.path.getsize(path) if os.path.exists(path) else 0,
        }
    return {
        "db_path": db_path,
        "db_size": db_size,
        "session_info": session_info,
    }




@app.route("/")
def index():
    base_dir, settings, db_path = _load_settings_and_db()

    enabled = settings.get("platforms", {}).get("enabled", [])
    platform_enabled = {
        "linkedin": "linkedin" in enabled,
        "indeed": "indeed" in enabled,
        "naukri": "naukri" in enabled,
    }
    use_ai = bool(settings.get("app", {}).get("use_ai", False))
    headless = bool(settings.get("app", {}).get("headless", True))
    run_interval = int(settings.get("app", {}).get("run_interval_seconds", 300))
    stats = _job_stats(db_path)
    health = _health_info(base_dir, db_path, settings)
    service_status = {
        "jobsentinel-linkedin": _service_container_status("jobsentinel-linkedin"),
        "jobsentinel-indeed": _service_container_status("jobsentinel-indeed"),
        "jobsentinel-naukri": _service_container_status("jobsentinel-naukri"),
    }
    service_labels = {
        key: _service_status_label(value) for key, value in service_status.items()
    }
    docker_available = _docker_client() is not None
    uptime = _human_duration(time.time() - START_TIME)
    profile_name = "cucia"
    profile = load_profile(base_dir, profile_name)
    messages = _load_recent_log(base_dir, limit=18)
    return render_template(
        "index.html",
        platform_enabled=platform_enabled,
        use_ai=use_ai,
        headless=headless,
        run_interval=run_interval,
        stats=stats,
        docker_available=docker_available,
        uptime=uptime,
        service_status=service_status,
        service_labels=service_labels,
        health=health,
        profile=profile,
        messages=messages,
        show_export=False,
    )


@app.route("/applied")
def applied():
    return jobs("applied")


@app.route("/review")
def review():
    return jobs("review")


@app.route("/queued")
def queued():
    return jobs("queued")


@app.route("/rejected")
def rejected():
    return jobs("rejected")


@app.route("/all")
def all_jobs():
    return jobs("all")


@app.route("/jobs/<status>")
def jobs(status: str):
    _base_dir, settings, db_path = _load_settings_and_db()

    allowed = {"all", "applied", "queued", "review", "rejected", "skipped", "deferred"}
    if status not in allowed:
        status = "all"
    statuses = None if status == "all" else [status]
    platform = request.args.get("platform", "").strip().lower()
    platform_filter = None
    if platform in {"linkedin", "indeed", "naukri"}:
        platform_filter = platform
    jobs = list_jobs(db_path, statuses=statuses, platform=platform_filter, limit=200)

    return render_template(
        "jobs.html",
        jobs=jobs,
        current_status=status,
        current_platform=platform_filter or "all",
        platforms=["all", "linkedin", "indeed", "naukri"],
        show_export=True,
    )



@app.get("/export.csv")
def export_csv():
    _base_dir, settings, db_path = _load_settings_and_db()

    status = request.args.get("status", "all")
    platform = request.args.get("platform", "").strip().lower()
    statuses = None if status == "all" else [status]
    platform_filter = platform if platform in {"linkedin", "indeed", "naukri"} else None
    jobs = list_jobs(db_path, statuses=statuses, platform=platform_filter, limit=1000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "job_key",
            "platform",
            "title",
            "company",
            "location",
            "job_url",
            "status",
            "easy_apply",
            "score",
            "decision",
            "posted_at",
            "posted_text",
            "created_at",
            "updated_at",
            "applied_at",
        ]
    )
    for job in jobs:
        writer.writerow(
            [
                job.get("job_key"),
                job.get("platform"),
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("job_url"),
                job.get("status"),
                job.get("easy_apply"),
                job.get("score"),
                job.get("decision"),
                job.get("posted_at"),
                job.get("posted_text"),
                job.get("created_at"),
                job.get("updated_at"),
                job.get("applied_at"),
            ]
        )

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = 'attachment; filename="jobs.csv"'
    return response


@app.post("/approve")
def approve():
    _base_dir, settings, db_path = _load_settings_and_db()

    job_key = request.form.get("job_key")
    if job_key:
        update_job(db_path, job_key, status="queued")
    
    status = request.form.get("current_status", "all")
    platform = request.form.get("current_platform", "")
    return redirect(url_for("jobs", status=status, platform=platform))


@app.post("/reject")
def reject():
    _base_dir, settings, db_path = _load_settings_and_db()

    job_key = request.form.get("job_key")
    if job_key:
        update_job(db_path, job_key, status="rejected")

    status = request.form.get("current_status", "all")
    platform = request.form.get("current_platform", "")
    return redirect(url_for("jobs", status=status, platform=platform))


@app.post("/mark-applied")
def mark_applied():
    _base_dir, settings, db_path = _load_settings_and_db()
    job_key = request.form.get("job_key")
    if job_key:
        update_job(db_path, job_key, status="applied")
    status = request.form.get("current_status", "all")
    platform = request.form.get("current_platform", "")
    return redirect(url_for("jobs", status=status, platform=platform))


@app.post("/agent/chat")
def agent_chat():
    message = (request.form.get("message") or "").strip()
    if not message:
        return redirect(url_for("index"))
    profile_name = request.form.get("profile_name", "cucia")
    handle_chat(message, profile_name)
    return redirect(url_for("index"))


@app.post("/toggle/platform/<platform>")
def toggle_platform(platform: str):
    base_dir, settings, _db_path = _load_settings_and_db()
    platforms_cfg = settings.setdefault("platforms", {})
    enabled = set(platforms_cfg.get("enabled", []))

    if platform in enabled:
        enabled.remove(platform)
    else:
        enabled.add(platform)

    platforms_cfg["enabled"] = sorted(enabled)
    save_settings(base_dir, settings)
    return redirect(url_for("index"))


@app.post("/toggle/ai")
def toggle_ai():
    base_dir, settings, _db_path = _load_settings_and_db()
    app_cfg = settings.setdefault("app", {})
    app_cfg["use_ai"] = not bool(app_cfg.get("use_ai", False))
    # Ensure enrichment is enabled when AI is turned on.
    if app_cfg["use_ai"]:
        app_cfg["enrich_before_ai"] = True
    save_settings(base_dir, settings)
    return redirect(url_for("index"))


@app.post("/service/start/<service>")
def start_service(service: str):
    client = _docker_client()
    if not client:
        return redirect(url_for("index"))
    try:
        containers = client.containers.list(all=True, filters={"label": f"com.docker.compose.service={service}"})
        if containers:
            containers[0].start()
    except Exception:
        pass
    return redirect(url_for("index"))


@app.post("/service/stop/<service>")
def stop_service(service: str):
    client = _docker_client()
    if not client:
        return redirect(url_for("index"))
    try:
        containers = client.containers.list(all=True, filters={"label": f"com.docker.compose.service={service}"})
        if containers:
            containers[0].stop()
    except Exception:
        pass
    return redirect(url_for("index"))


def main() -> None:
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()

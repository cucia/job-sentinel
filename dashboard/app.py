import csv
import io
import os

from flask import Flask, request, redirect, url_for, render_template, Response

from core.config import load_settings, save_settings
from core.storage import init_db, list_jobs, update_job

app = Flask(__name__)


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




@app.route("/")
def index():
    base_dir, settings, db_path = _load_settings_and_db()

    status = request.args.get("status", "all")
    easy = request.args.get("easy", "")
    statuses = None if status == "all" else [status]
    easy_filter = True if easy == "1" else None
    jobs = list_jobs(db_path, statuses=statuses, easy_apply=easy_filter, limit=200)
    enabled = settings.get("platforms", {}).get("enabled", [])
    platform_enabled = {
        "linkedin": "linkedin" in enabled,
        "naukri": "naukri" in enabled,
    }
    use_ai = bool(settings.get("app", {}).get("use_ai", False))
    return render_template(
        "index.html",
        jobs=jobs,
        current_status=status,
        current_easy=easy,
        platform_enabled=platform_enabled,
        use_ai=use_ai,
    )


@app.get("/export.csv")
def export_csv():
    _base_dir, settings, db_path = _load_settings_and_db()

    status = request.args.get("status", "all")
    easy = request.args.get("easy", "")
    statuses = None if status == "all" else [status]
    easy_filter = True if easy == "1" else None
    jobs = list_jobs(db_path, statuses=statuses, easy_apply=easy_filter, limit=1000)

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
    return redirect(url_for("index"))


@app.post("/reject")
def reject():
    _base_dir, settings, db_path = _load_settings_and_db()

    job_key = request.form.get("job_key")
    if job_key:
        update_job(db_path, job_key, status="rejected")
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


def main() -> None:
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()

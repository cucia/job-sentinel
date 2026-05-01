import csv
import io
import os
import sqlite3
import time
from datetime import datetime, timezone

import docker
from flask import Flask, request, redirect, url_for, render_template, Response
from flask_socketio import SocketIO

from src.ai.profile_store import save_profile
from src.ai.scorer import update_model
from src.ai.chat import handle_chat, _load_recent_log
from src.core.config import default_profile_name, load_profile, load_settings, save_settings
from src.core.logger import log
from src.core.platform_registry import get_platforms
from src.services.session_manager import (
    cancel_session_login,
    delete_session_file,
    login_linkedin_with_credentials,
    session_overview,
    start_session_login,
    save_session_login,
    validate_saved_session,
)
from src.core.storage import (
    get_approved_count,
    get_feedback_label,
    get_job,
    get_model_state,
    init_db,
    list_jobs,
    record_feedback,
    save_model_state,
    update_job,
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jobsentinel-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
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


def _selected_profile_name(base_dir: str) -> str:
    return _profile_key(
        request.values.get("profile") or request.values.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )


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


def _profile_key(name: str | None, fallback: str = "candidate") -> str:
    safe = (name or "").strip().lower().replace(" ", "_")
    return safe or fallback


def _list_profiles(base_dir: str) -> list[str]:
    profiles_dir = os.path.join(base_dir, "profiles")
    names: list[str] = []
    if os.path.isdir(profiles_dir):
        names = sorted(
            os.path.splitext(name)[0]
            for name in os.listdir(profiles_dir)
            if name.endswith(".yaml")
        )
    default_name = default_profile_name(base_dir)
    if default_name not in names:
        names.insert(0, default_name)
    return names


def _parse_list_field(raw: str) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for part in (raw or "").replace("\r", "\n").replace(",", "\n").split("\n"):
        value = part.strip()
        normalized = value.lower()
        if not value or normalized in seen:
            continue
        items.append(value)
        seen.add(normalized)
    return items


def _parse_bool_field(raw: str):
    value = (raw or "").strip().lower()
    if value in {"true", "yes", "1"}:
        return True
    if value in {"false", "no", "0"}:
        return False
    return ""


def _redirect_index(profile_name: str, notice: str = "", notice_level: str = "ok"):
    return _redirect_page("index", profile_name, notice=notice, notice_level=notice_level)


def _redirect_page(
    endpoint: str,
    profile_name: str,
    notice: str = "",
    notice_level: str = "ok",
    **params,
):
    redirect_params = dict(params)
    if profile_name:
        redirect_params["profile"] = profile_name
    if notice:
        redirect_params["notice"] = notice
        redirect_params["notice_level"] = notice_level
    return redirect(url_for(endpoint, **redirect_params))


def _redirect_jobs(status: str, platform: str, notice: str = "", notice_level: str = "ok"):
    params = {"status": status or "all"}
    if platform and platform != "all":
        params["platform"] = platform
    if notice:
        params["notice"] = notice
        params["notice_level"] = notice_level
    return redirect(url_for("jobs", **params))


def _vnc_url() -> str:
    return (os.environ.get("JOBSENTINEL_VNC_URL") or "").strip()


def _resolve_resume_path(base_dir: str, settings: dict) -> str:
    resume_path = settings.get("app", {}).get("resume_path", "resumes/resume.pdf")
    if os.path.isabs(resume_path):
        return resume_path
    return os.path.join(base_dir, resume_path)


def _pipeline_mode(settings: dict) -> str:
    return (settings.get("app", {}).get("pipeline_mode") or "direct_latest").strip().lower()


def _model_info(db_path: str) -> dict:
    state = get_model_state(db_path)
    return {
        "trained_examples": int(state.get("trained_examples", 0) or 0),
        "feature_count": len(state.get("weights", {}) or {}),
        "bias": round(float(state.get("bias", 0.0) or 0.0), 2),
        "approved_count": get_approved_count(db_path),
    }


def _inverse_feedback_label(label: str | None) -> str | None:
    normalized = (label or "").strip().lower()
    if normalized in {"approved", "applied", "positive"}:
        return "rejected"
    if normalized in {"rejected", "negative", "skipped"}:
        return "approved"
    return None


def _load_recent_text_log(base_dir: str, limit: int = 200) -> list[str]:
    log_path = os.path.join(base_dir, "data", "jobsentinel.log")
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f.readlines()[-limit:]]


def _get_agent_activity(db_path: str) -> list:
    """Get recent agent activity from jobs table."""
    activity = []
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("""
            SELECT title, company, decision, score, created_at
            FROM jobs
            WHERE decision IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 20
        """).fetchall()

        for row in rows:
            title, company, decision, score, created_at = row

            # Parse timestamp
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                timestamp = dt.strftime('%H:%M:%S')
            except:
                timestamp = created_at[:8] if created_at else 'N/A'

            # Determine agent and action
            agent = "JobEvaluatorAgent"
            action = f"Evaluated '{title[:30]}...' at {company or 'Unknown'}"
            result = decision or "REVIEW"

            activity.append({
                'timestamp': timestamp,
                'agent': agent,
                'action': action,
                'result': result
            })

    return activity


def _get_analytics_data(db_path: str) -> dict:
    """Get analytics data for charts and metrics."""
    from datetime import datetime, timedelta

    with sqlite3.connect(db_path) as conn:
        # Pipeline data
        pipeline_data = []
        for status in ['total', 'queued', 'review', 'applied', 'rejected', 'skipped']:
            if status == 'total':
                count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            else:
                count = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = ?", (status,)).fetchone()[0]
            pipeline_data.append(count)

        # Trends data (last 7 days)
        trends_labels = []
        trends_data = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            trends_labels.append(date)
            count = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status = 'applied' AND substr(applied_at, 1, 10) = ?",
                (date,)
            ).fetchone()[0]
            trends_data.append(count)

        # Platform data
        platform_labels = []
        platform_data = []
        platforms = conn.execute(
            "SELECT platform, COUNT(*) FROM jobs WHERE status = 'applied' GROUP BY platform"
        ).fetchall()
        for platform, count in platforms:
            platform_labels.append((platform or 'unknown').capitalize())
            platform_data.append(count)

        # Agent stats
        total_evals = conn.execute("SELECT COUNT(*) FROM jobs WHERE score IS NOT NULL").fetchone()[0] or 1

        avg_confidence = 0  # Confidence data not available in current schema

        apply_count = conn.execute("SELECT COUNT(*) FROM jobs WHERE decision = 'APPLY'").fetchone()[0] or 0
        review_count = conn.execute("SELECT COUNT(*) FROM jobs WHERE decision = 'REVIEW'").fetchone()[0] or 0

        applied_count = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'").fetchone()[0] or 0
        rejected_count = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'rejected'").fetchone()[0] or 0

        success_rate = round((applied_count / max(applied_count + rejected_count, 1)) * 100, 1)

        agent_stats = {
            'total_evaluations': total_evals,
            'avg_confidence': round(avg_confidence, 1),
            'apply_count': apply_count,
            'apply_rate': round((apply_count / total_evals) * 100, 1),
            'review_count': review_count,
            'review_rate': round((review_count / total_evals) * 100, 1),
            'success_rate': success_rate
        }

        # Recent decisions
        recent_decisions = []
        try:
            rows = conn.execute("""
                SELECT title, company, platform, score, decision, created_at
                FROM jobs
                WHERE decision IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 10
            """).fetchall()

            for row in rows:
                title, company, platform, score, decision, created_at = row

                recent_decisions.append({
                    'job_title': title or 'Unknown',
                    'company': company or 'Unknown',
                    'platform': (platform or 'unknown').capitalize(),
                    'score': score or 0,
                    'confidence': 0,
                    'decision': decision or 'REVIEW',
                    'reasoning': '',
                    'match_factors': [],
                    'concerns': []
                })
        except Exception as e:
            log(f"Error fetching recent decisions: {e}")
            recent_decisions = []

    return {
        'pipeline_data': pipeline_data,
        'trends_labels': trends_labels,
        'trends_data': trends_data,
        'platform_labels': platform_labels,
        'platform_data': platform_data,
        'agent_stats': agent_stats,
        'recent_decisions': recent_decisions
    }


def _dashboard_context(base_dir: str, settings: dict, db_path: str) -> dict:
    enabled = settings.get("platforms", {}).get("enabled", [])
    platform_enabled = {
        "linkedin": "linkedin" in enabled,
        "indeed": "indeed" in enabled,
        "naukri": "naukri" in enabled,
    }
    use_ai = bool(settings.get("app", {}).get("use_ai", False))
    use_llm = bool(settings.get("ai", {}).get("use_llm", False))
    llm_model = settings.get("ai", {}).get("llm_model", "llama3.2:latest")
    headless = bool(settings.get("app", {}).get("headless", True))
    run_interval = int(settings.get("app", {}).get("run_interval_seconds", 300))
    pipeline_mode = _pipeline_mode(settings)
    latest_results_limit = int(settings.get("app", {}).get("latest_results_limit", 100))
    easy_apply_first = bool(settings.get("app", {}).get("easy_apply_first", True))
    history_limit = int(settings.get("storage", {}).get("history_limit", 400))
    linkedin_easy_apply_only = bool(
        settings.get("platforms", {}).get("linkedin", {}).get("search", {}).get("easy_apply_only", False)
    )
    stats = _job_stats(db_path)
    health = _health_info(base_dir, db_path, settings)
    model_info = _model_info(db_path)
    service_status = {
        "jobsentinel-linkedin": _service_container_status("jobsentinel-linkedin"),
        "jobsentinel-indeed": _service_container_status("jobsentinel-indeed"),
        "jobsentinel-naukri": _service_container_status("jobsentinel-naukri"),
    }
    service_labels = {key: _service_status_label(value) for key, value in service_status.items()}
    docker_available = _docker_client() is not None
    uptime = _human_duration(time.time() - START_TIME)
    profile_name = _selected_profile_name(base_dir)
    profile_names = _list_profiles(base_dir)
    if profile_name not in profile_names:
        profile_names.append(profile_name)
        profile_names.sort()
    profile = load_profile(base_dir, profile_name)
    session_info = session_overview(base_dir, settings)
    session_ready_count = sum(
        1 for info in session_info.get("platforms", {}).values() if info.get("login_status") == "ready"
    )

    # Check Ollama status
    try:
        from src.ai.llm import check_ollama_status
        ollama_status = check_ollama_status()
    except Exception:
        ollama_status = {"available": False, "models": [], "default": "llama3.2:latest"}

    return {
        "platform_enabled": platform_enabled,
        "use_ai": use_ai,
        "headless": headless,
        "run_interval": run_interval,
        "pipeline_mode": pipeline_mode,
        "latest_results_limit": latest_results_limit,
        "easy_apply_first": easy_apply_first,
        "history_limit": history_limit,
        "linkedin_easy_apply_only": linkedin_easy_apply_only,
        "stats": stats,
        "docker_available": docker_available,
        "uptime": uptime,
        "service_status": service_status,
        "service_labels": service_labels,
        "health": health,
        "model_info": model_info,
        "profile": profile,
        "profile_name": profile_name,
        "profile_names": profile_names,
        "session_info": session_info,
        "session_ready_count": session_ready_count,
        "ollama_status": ollama_status,
        "use_llm": use_llm,
        "llm_model": llm_model,
        "vnc_url": _vnc_url(),
        "messages": _load_recent_log(base_dir, limit=18),
        "notice": (request.args.get("notice") or "").strip(),
        "notice_level": (request.args.get("notice_level") or "ok").strip().lower(),
    }


def _apply_feedback_learning(base_dir: str, db_path: str, job_key: str, label: str, source: str) -> None:
    previous_label = get_feedback_label(db_path, job_key)
    record_feedback(db_path, job_key, label, source=source)
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


def _run_dashboard_apply(base_dir: str, settings: dict, db_path: str, job: dict) -> tuple[str, str]:
    apply_fn = get_platforms().get(job.get("platform"))
    if not apply_fn:
        return "warn", "No apply module is registered for this platform."

    resume_path = _resolve_resume_path(base_dir, settings)
    try:
        result = apply_fn(job, resume_path, settings)
    except Exception as exc:
        log(f"Dashboard apply failed for {job.get('job_key')}: {exc}")
        update_job(db_path, job["job_key"], status="review", easy_apply=0)
        return "warn", f"Apply attempt failed: {exc}"

    result_status = None
    easy_apply = None
    if isinstance(result, tuple):
        result_status, easy_apply = result

    if result_status == "applied":
        update_job(db_path, job["job_key"], status="applied", easy_apply=easy_apply)
        return "ok", "Application submitted successfully."
    if result_status == "review":
        update_job(db_path, job["job_key"], status="review", easy_apply=easy_apply)
        return "warn", "Apply flow needs review. Open the job and finish any missing answers manually."
    if result_status == "skipped":
        update_job(db_path, job["job_key"], status="skipped", easy_apply=easy_apply)
        return "warn", "Job was skipped by the apply module."

    update_job(db_path, job["job_key"], status="deferred", easy_apply=easy_apply)
    return "warn", "Apply attempt was deferred."




@app.route("/")
def index():
    # Redirect to command center as the new default
    return redirect(url_for('command_center'))


@app.route("/command-center")
def command_center():
    base_dir, settings, db_path = _load_settings_and_db()
    context = _dashboard_context(base_dir, settings, db_path)

    # Get jobs for queue (review, queued, deferred)
    jobs = list_jobs(db_path, statuses=['review', 'queued', 'deferred'], limit=50)

    # Get recent agent activity (mock for now, will be populated by real agent logs)
    agent_activity = _get_agent_activity(db_path)

    # Get daily limit
    limits_daily = settings.get('limits', {}).get('daily_applications', 10)

    context.update({
        'jobs': jobs,
        'agent_activity': agent_activity,
        'limits_daily': limits_daily
    })

    return render_template("command_center.html", current_page="command", show_export=False, **context)


@app.route("/automation")
def automation():
    base_dir, settings, db_path = _load_settings_and_db()
    context = _dashboard_context(base_dir, settings, db_path)
    return render_template("automation.html", current_page="automation", show_export=False, **context)


@app.route("/analytics")
def analytics():
    base_dir, settings, db_path = _load_settings_and_db()
    context = _dashboard_context(base_dir, settings, db_path)

    # Get analytics data
    analytics_data = _get_analytics_data(db_path)
    context.update(analytics_data)

    return render_template("analytics.html", current_page="analytics", show_export=False, **context)


@app.route("/agents")
def agents():
    base_dir, settings, db_path = _load_settings_and_db()
    context = _dashboard_context(base_dir, settings, db_path)

    # Get agent activity and analytics
    agent_activity = _get_agent_activity(db_path)
    analytics_data = _get_analytics_data(db_path)

    # Get agent configuration
    use_agents = settings.get('ai', {}).get('use_agents', False)
    use_multi_agent = settings.get('ai', {}).get('use_multi_agent', False)
    use_cloud = settings.get('ai', {}).get('use_cloud', False)
    provider = settings.get('ai', {}).get('provider', 'groq')
    model = settings.get('ai', {}).get('model', 'llama-3.1-8b-instant')

    context.update({
        'agent_activity': agent_activity,
        'agent_stats': analytics_data.get('agent_stats', {}),
        'recent_decisions': analytics_data.get('recent_decisions', []),
        'use_agents': use_agents,
        'use_multi_agent': use_multi_agent,
        'use_cloud': use_cloud,
        'provider': provider,
        'model': model,
    })

    return render_template("agents.html", current_page="agents", show_export=False, **context)


@app.route("/sessions")
def sessions_page():
    base_dir, settings, db_path = _load_settings_and_db()
    context = _dashboard_context(base_dir, settings, db_path)
    return render_template("sessions.html", current_page="sessions", show_export=False, **context)


@app.route("/profile")
def profile_page():
    base_dir, settings, db_path = _load_settings_and_db()
    context = _dashboard_context(base_dir, settings, db_path)
    return render_template("profile.html", current_page="profile", show_export=False, **context)


@app.post("/bulk-approve")
def bulk_approve():
    base_dir, settings, db_path = _load_settings_and_db()
    data = request.get_json()
    job_keys = data.get('job_keys', [])

    for job_key in job_keys:
        _apply_feedback_learning(base_dir, db_path, job_key, "approved", "bulk")
        if _pipeline_mode(settings) == "direct_latest":
            job = get_job(db_path, job_key)
            if job:
                _run_dashboard_apply(base_dir, settings, db_path, job)
        else:
            update_job(db_path, job_key, status="queued")

    return {"status": "success", "count": len(job_keys)}


@app.post("/bulk-reject")
def bulk_reject():
    base_dir, settings, db_path = _load_settings_and_db()
    data = request.get_json()
    job_keys = data.get('job_keys', [])

    for job_key in job_keys:
        _apply_feedback_learning(base_dir, db_path, job_key, "rejected", "bulk")
        update_job(db_path, job_key, status="rejected")

    return {"status": "success", "count": len(job_keys)}


@app.post("/quick-approve")
def quick_approve():
    base_dir, settings, db_path = _load_settings_and_db()
    data = request.get_json()
    job_key = data.get('job_key')

    if job_key:
        _apply_feedback_learning(base_dir, db_path, job_key, "approved", "quick")
        if _pipeline_mode(settings) == "direct_latest":
            job = get_job(db_path, job_key)
            if job:
                _run_dashboard_apply(base_dir, settings, db_path, job)
        else:
            update_job(db_path, job_key, status="queued")

    return {"status": "success"}


@app.post("/quick-reject")
def quick_reject():
    base_dir, settings, db_path = _load_settings_and_db()
    data = request.get_json()
    job_key = data.get('job_key')

    if job_key:
        _apply_feedback_learning(base_dir, db_path, job_key, "rejected", "quick")
        update_job(db_path, job_key, status="rejected")

    return {"status": "success"}


@app.post("/toggle/easy-apply")
def toggle_easy_apply():
    base_dir, settings, db_path = _load_settings_and_db()
    app_cfg = settings.setdefault("app", {})
    app_cfg["easy_apply_first"] = not bool(app_cfg.get("easy_apply_first", True))
    save_settings(base_dir, settings)
    return {"status": "success"}


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


@app.route("/skipped")
def skipped():
    return jobs("skipped")


@app.route("/deferred")
def deferred():
    return jobs("deferred")


@app.route("/all")
def all_jobs():
    return jobs("all")


@app.route("/jobs/<status>")
def jobs(status: str):
    base_dir, settings, db_path = _load_settings_and_db()

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
        statuses=["all", "review", "applied", "deferred", "rejected", "skipped", "queued"],
        platforms=["all", "linkedin", "indeed", "naukri"],
        pipeline_mode=_pipeline_mode(settings),
        notice=(request.args.get("notice") or "").strip(),
        notice_level=(request.args.get("notice_level") or "ok").strip().lower(),
        profile_name=_selected_profile_name(base_dir),
        current_page="jobs",
        show_export=True,
    )


@app.route("/logs")
def logs():
    base_dir, settings, db_path = _load_settings_and_db()
    return render_template(
        "logs.html",
        log_lines=_load_recent_text_log(base_dir),
        notice=(request.args.get("notice") or "").strip(),
        notice_level=(request.args.get("notice_level") or "ok").strip().lower(),
        profile_name=_selected_profile_name(base_dir),
        current_page="logs",
        show_export=False,
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
            "feedback_label",
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
                job.get("feedback_label"),
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
    base_dir, settings, db_path = _load_settings_and_db()

    job_key = request.form.get("job_key")
    status = request.form.get("current_status", "all")
    platform = request.form.get("current_platform", "")
    if job_key:
        _apply_feedback_learning(base_dir, db_path, job_key, "approved", "dashboard")
        if _pipeline_mode(settings) == "direct_latest":
            job = get_job(db_path, job_key)
            if not job:
                return _redirect_jobs(status, platform, "Job not found.", "warn")
            notice_level, message = _run_dashboard_apply(base_dir, settings, db_path, job)
            return _redirect_jobs(status, platform, f"Job approved. {message}", notice_level)
        update_job(db_path, job_key, status="queued")

    return _redirect_jobs(status, platform, "Job approved and moved to queued.", "ok")


@app.post("/reject")
def reject():
    base_dir, settings, db_path = _load_settings_and_db()

    job_key = request.form.get("job_key")
    if job_key:
        _apply_feedback_learning(base_dir, db_path, job_key, "rejected", "dashboard")
        update_job(db_path, job_key, status="rejected")

    status = request.form.get("current_status", "all")
    platform = request.form.get("current_platform", "")
    return _redirect_jobs(status, platform, "Job rejected.", "ok")


@app.post("/mark-applied")
def mark_applied():
    base_dir, settings, db_path = _load_settings_and_db()
    job_key = request.form.get("job_key")
    if job_key:
        _apply_feedback_learning(base_dir, db_path, job_key, "applied", "dashboard")
        update_job(db_path, job_key, status="applied")
    status = request.form.get("current_status", "all")
    platform = request.form.get("current_platform", "")
    return _redirect_jobs(status, platform, "Job marked as applied.", "ok")


@app.post("/attempt-apply")
def attempt_apply():
    base_dir, settings, db_path = _load_settings_and_db()
    job_key = request.form.get("job_key")
    status = request.form.get("current_status", "all")
    platform = request.form.get("current_platform", "")
    if not job_key:
        return _redirect_jobs(status, platform, "Missing job key.", "warn")

    job = get_job(db_path, job_key)
    if not job:
        return _redirect_jobs(status, platform, "Job not found.", "warn")

    notice_level, message = _run_dashboard_apply(base_dir, settings, db_path, job)
    return _redirect_jobs(status, platform, message, notice_level)


@app.post("/agent/chat")
def agent_chat():
    message = (request.form.get("message") or "").strip()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(_base_dir()),
    )
    if not message:
        return _redirect_page("profile_page", profile_name)
    base_dir = _base_dir()
    handle_chat(message, profile_name)
    return _redirect_page("profile_page", profile_name, "Assistant context updated.", "ok")


@app.post("/profile/save")
def save_profile_details():
    base_dir, _settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    profile = load_profile(base_dir, profile_name)
    profile.update(
        {
            "name": (request.form.get("name") or "").strip() or profile_name.replace("_", " ").title(),
            "role": (request.form.get("role") or "").strip(),
            "experience": (request.form.get("experience") or "").strip(),
            "location": (request.form.get("location") or "").strip(),
            "email": (request.form.get("email") or "").strip(),
            "phone": (request.form.get("phone") or "").strip(),
            "current_company": (request.form.get("current_company") or "").strip(),
            "notice_period_days": (request.form.get("notice_period_days") or "").strip(),
            "current_ctc": (request.form.get("current_ctc") or "").strip(),
            "expected_ctc": (request.form.get("expected_ctc") or "").strip(),
            "available_to_start": (request.form.get("available_to_start") or "").strip(),
            "education": (request.form.get("education") or "").strip(),
            "linkedin_url": (request.form.get("linkedin_url") or "").strip(),
            "github_url": (request.form.get("github_url") or "").strip(),
            "portfolio_url": (request.form.get("portfolio_url") or "").strip(),
            "work_authorization": _parse_bool_field(request.form.get("work_authorization") or ""),
            "sponsorship_required": _parse_bool_field(request.form.get("sponsorship_required") or ""),
            "willing_to_relocate": _parse_bool_field(request.form.get("willing_to_relocate") or ""),
            "willing_to_work_onsite": _parse_bool_field(request.form.get("willing_to_work_onsite") or ""),
            "willing_to_work_shifts": _parse_bool_field(request.form.get("willing_to_work_shifts") or ""),
            "willing_to_travel": _parse_bool_field(request.form.get("willing_to_travel") or ""),
            "skills": _parse_list_field(request.form.get("skills") or ""),
            "keywords": _parse_list_field(request.form.get("keywords") or ""),
        }
    )
    save_profile(base_dir, profile_name, profile)
    return _redirect_page("profile_page", profile_name, "Profile details saved.", "ok")


@app.post("/upload-resume")
def upload_resume():
    """Handle resume upload and parse data into profile."""
    base_dir, _settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )

    if 'resume' not in request.files:
        return _redirect_page("profile_page", profile_name, "No resume file uploaded.", "warn")

    file = request.files['resume']
    if file.filename == '':
        return _redirect_page("profile_page", profile_name, "No resume file selected.", "warn")

    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return _redirect_page("profile_page", profile_name, "Invalid file type. Use PDF, DOCX, or TXT.", "warn")

    try:
        import tempfile
        from src.ai.resume_parser import parse_resume
        from src.ai.profile_store import init_profile_from_resume, update_profile_fields

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            resume_data = parse_resume(tmp_path, use_llm=True)
            new_profile = init_profile_from_resume(base_dir, resume_data)
            update_profile_fields(base_dir, profile_name, new_profile)
            return _redirect_page("profile_page", profile_name, "Resume parsed successfully! Review and save the extracted data.", "ok")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        log(f"Resume parsing error: {e}")
        return _redirect_page("profile_page", profile_name, f"Error parsing resume: {str(e)}", "warn")


@app.post("/session/start/<platform>")
def session_start(platform: str):
    base_dir, settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    ok, message = start_session_login(base_dir, settings, platform)
    return _redirect_page("sessions_page", profile_name, message, "ok" if ok else "warn")


@app.post("/session/save/<platform>")
def session_save(platform: str):
    base_dir, _settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    ok, message = save_session_login(platform)
    return _redirect_page("sessions_page", profile_name, message, "ok" if ok else "warn")


@app.post("/session/check/<platform>")
def session_check(platform: str):
    base_dir, settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    ok, message = validate_saved_session(base_dir, settings, platform)
    return _redirect_page("sessions_page", profile_name, message, "ok" if ok else "warn")


@app.post("/session/linkedin/login")
def session_linkedin_login():
    base_dir, settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    email = request.form.get("linkedin_email") or ""
    password = request.form.get("linkedin_password") or ""
    ok, message = login_linkedin_with_credentials(base_dir, settings, email, password)
    return _redirect_page("sessions_page", profile_name, message, "ok" if ok else "warn")


@app.post("/session/cancel/<platform>")
def session_cancel(platform: str):
    base_dir, _settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    ok, message = cancel_session_login(platform)
    return _redirect_page("sessions_page", profile_name, message, "ok" if ok else "warn")


@app.post("/session/delete/<platform>")
def session_delete(platform: str):
    base_dir, settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    ok, message = delete_session_file(base_dir, settings, platform)
    return _redirect_page("sessions_page", profile_name, message, "ok" if ok else "warn")


@app.post("/toggle/platform/<platform>")
def toggle_platform(platform: str):
    base_dir, settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    platforms_cfg = settings.setdefault("platforms", {})
    enabled = set(platforms_cfg.get("enabled", []))

    if platform in enabled:
        enabled.remove(platform)
    else:
        enabled.add(platform)

    platforms_cfg["enabled"] = sorted(enabled)
    save_settings(base_dir, settings)
    return _redirect_page("automation", profile_name, f"{platform.capitalize()} toggled.", "ok")


@app.post("/toggle/ai")
def toggle_ai():
    base_dir, settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    app_cfg = settings.setdefault("app", {})
    app_cfg["use_ai"] = not bool(app_cfg.get("use_ai", False))
    # Ensure enrichment is enabled when AI is turned on.
    if app_cfg["use_ai"]:
        app_cfg["enrich_before_ai"] = True
    save_settings(base_dir, settings)
    return _redirect_page("automation", profile_name, f"AI filter turned {'on' if app_cfg['use_ai'] else 'off'}.", "ok")


@app.post("/toggle/llm")
def toggle_llm():
    base_dir, settings, _db_path = _load_settings_and_db()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(base_dir),
    )
    ai_cfg = settings.setdefault("ai", {})
    ai_cfg["use_llm"] = not bool(ai_cfg.get("use_llm", False))
    save_settings(base_dir, settings)
    return _redirect_page("automation", profile_name, f"LLM evaluation turned {'on' if ai_cfg['use_llm'] else 'off'}.", "ok")


@app.post("/service/start/<service>")
def start_service(service: str):
    client = _docker_client()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(_base_dir()),
    )
    if not client:
        return _redirect_page("automation", profile_name, "Docker is unavailable for service control.", "warn")
    try:
        containers = client.containers.list(all=True, filters={"label": f"com.docker.compose.service={service}"})
        if containers:
            containers[0].start()
    except Exception:
        pass
    return _redirect_page("automation", profile_name, f"Requested start for {service}.", "ok")


@app.post("/service/stop/<service>")
def stop_service(service: str):
    client = _docker_client()
    profile_name = _profile_key(
        request.form.get("profile_name"),
        fallback=default_profile_name(_base_dir()),
    )
    if not client:
        return _redirect_page("automation", profile_name, "Docker is unavailable for service control.", "warn")
    try:
        containers = client.containers.list(all=True, filters={"label": f"com.docker.compose.service={service}"})
        if containers:
            containers[0].stop()
    except Exception:
        pass
    return _redirect_page("automation", profile_name, f"Requested stop for {service}.", "ok")


def main() -> None:
    # Start background updates for WebSocket
    base_dir = _base_dir()
    settings = load_settings(base_dir)
    db_path = _resolve_db_path(base_dir, settings)

    from dashboard.websocket_handler import start_background_updates
    start_background_updates(socketio, db_path, interval=10)

    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()

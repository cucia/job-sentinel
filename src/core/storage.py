import json
import os
import sqlite3
from datetime import datetime


def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


def init_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_key TEXT UNIQUE,
                platform TEXT,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                job_url TEXT,
                status TEXT,
                easy_apply INTEGER,
                score INTEGER,
                decision TEXT,
                posted_at TEXT,
                posted_text TEXT,
                created_at TEXT,
                updated_at TEXT,
                applied_at TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                job_key TEXT PRIMARY KEY,
                label TEXT,
                notes TEXT,
                source TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS model_state (
                name TEXT PRIMARY KEY,
                weights_json TEXT,
                bias REAL,
                trained_examples INTEGER,
                updated_at TEXT
            );
            """
        )
        cur = conn.execute("PRAGMA table_info(jobs)")
        columns = {row[1] for row in cur.fetchall()}
        if "easy_apply" not in columns:
            conn.execute("ALTER TABLE jobs ADD COLUMN easy_apply INTEGER")
        if "posted_at" not in columns:
            conn.execute("ALTER TABLE jobs ADD COLUMN posted_at TEXT")
        if "posted_text" not in columns:
            conn.execute("ALTER TABLE jobs ADD COLUMN posted_text TEXT")
        conn.commit()


def has_seen_job(db_path: str, job_key: str) -> bool:
    with _connect(db_path) as conn:
        cur = conn.execute("SELECT 1 FROM jobs WHERE job_key = ? LIMIT 1", (job_key,))
        return cur.fetchone() is not None


def upsert_job(
    db_path: str,
    job: dict,
    status: str,
    easy_apply: int | None = None,
    score: int | None = None,
    decision: str | None = None,
) -> None:
    now = datetime.utcnow().isoformat()
    applied_at = now if status == "applied" else None
    resolved_easy_apply = easy_apply
    if resolved_easy_apply is None and job.get("easy_apply") is not None:
        resolved_easy_apply = int(job.get("easy_apply") or 0)
    with _connect(db_path) as conn:
        posted_at = job.get("posted_at") or None
        posted_text = job.get("posted_text") or None
        conn.execute(
            """
            INSERT INTO jobs (
                job_key, platform, title, company, location, description, job_url,
                status, easy_apply, score, decision, posted_at, posted_text,
                created_at, updated_at, applied_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_key) DO UPDATE SET
                platform = excluded.platform,
                title = COALESCE(NULLIF(excluded.title, ''), jobs.title),
                company = COALESCE(NULLIF(excluded.company, ''), jobs.company),
                location = COALESCE(NULLIF(excluded.location, ''), jobs.location),
                description = COALESCE(NULLIF(excluded.description, ''), jobs.description),
                job_url = COALESCE(NULLIF(excluded.job_url, ''), jobs.job_url),
                status = excluded.status,
                easy_apply = COALESCE(excluded.easy_apply, jobs.easy_apply),
                score = COALESCE(excluded.score, jobs.score),
                decision = COALESCE(NULLIF(excluded.decision, ''), jobs.decision),
                posted_at = COALESCE(NULLIF(excluded.posted_at, ''), jobs.posted_at),
                posted_text = COALESCE(NULLIF(excluded.posted_text, ''), jobs.posted_text),
                updated_at = excluded.updated_at,
                applied_at = COALESCE(excluded.applied_at, jobs.applied_at)
            """,
            (
                job.get("job_key"),
                job.get("platform"),
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("description"),
                job.get("job_url"),
                status,
                resolved_easy_apply,
                score,
                decision,
                posted_at,
                posted_text,
                now,
                now,
                applied_at,
            ),
        )
        conn.commit()


def enqueue_job(db_path: str, job: dict) -> None:
    upsert_job(db_path, job, status="queued")


def next_queued_job(db_path: str) -> dict | None:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT job_key, platform, title, company, location, description, job_url
            FROM jobs
            WHERE status = 'queued'
            ORDER BY created_at ASC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "job_key": row[0],
            "platform": row[1],
            "title": row[2],
            "company": row[3],
            "location": row[4],
            "description": row[5],
            "job_url": row[6],
        }


def get_job(db_path: str, job_key: str) -> dict | None:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT
                j.job_key, j.platform, j.title, j.company, j.location, j.description, j.job_url,
                j.status, j.easy_apply, j.score, j.decision, j.posted_at, j.posted_text,
                j.created_at, j.updated_at, j.applied_at, f.label
            FROM jobs j
            LEFT JOIN feedback f ON f.job_key = j.job_key
            WHERE j.job_key = ?
            LIMIT 1
            """,
            (job_key,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "job_key": row[0],
        "platform": row[1],
        "title": row[2],
        "company": row[3],
        "location": row[4],
        "description": row[5],
        "job_url": row[6],
        "status": row[7],
        "easy_apply": row[8],
        "score": row[9],
        "decision": row[10],
        "posted_at": row[11],
        "posted_text": row[12],
        "created_at": row[13],
        "updated_at": row[14],
        "applied_at": row[15],
        "feedback_label": row[16],
    }


def update_job(db_path: str, job_key: str, **fields) -> None:
    if not fields:
        return
    now = datetime.utcnow().isoformat()
    fields["updated_at"] = now
    if fields.get("status") == "applied":
        fields["applied_at"] = now
    columns = ", ".join([f"{k} = ?" for k in fields.keys()])
    values = list(fields.values()) + [job_key]
    with _connect(db_path) as conn:
        conn.execute(f"UPDATE jobs SET {columns} WHERE job_key = ?", values)
        conn.commit()


def record_decision(db_path: str, job_key: str, decision: str, score: int) -> None:
    update_job(db_path, job_key, decision=decision, score=score)


def get_daily_apply_count(db_path: str, date_iso: str) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT COUNT(1)
            FROM jobs
            WHERE status = 'applied'
              AND substr(applied_at, 1, 10) = ?
            """,
            (date_iso,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0


def record_feedback(
    db_path: str,
    job_key: str,
    label: str,
    notes: str = "",
    source: str = "user",
) -> None:
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO feedback (job_key, label, notes, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_key) DO UPDATE SET
                label = excluded.label,
                notes = excluded.notes,
                source = excluded.source,
                updated_at = excluded.updated_at
            """,
            (job_key, label, notes, source, now, now),
        )
        conn.commit()


def get_feedback_label(db_path: str, job_key: str) -> str | None:
    with _connect(db_path) as conn:
        cur = conn.execute("SELECT label FROM feedback WHERE job_key = ? LIMIT 1", (job_key,))
        row = cur.fetchone()
        return row[0] if row else None


def get_approved_count(db_path: str) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT COUNT(1)
            FROM feedback
            WHERE label IN ('approved', 'applied', 'positive')
            """
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0


def get_model_state(db_path: str) -> dict:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT weights_json, bias, trained_examples
            FROM model_state
            WHERE name = 'default'
            LIMIT 1
            """
        )
        row = cur.fetchone()
    if not row:
        return {"weights": {}, "bias": 0.0, "trained_examples": 0}
    weights_json, bias, trained_examples = row
    try:
        weights = json.loads(weights_json or "{}")
    except json.JSONDecodeError:
        weights = {}
    return {
        "weights": weights,
        "bias": float(bias or 0.0),
        "trained_examples": int(trained_examples or 0),
    }


def save_model_state(
    db_path: str,
    weights: dict,
    bias: float,
    trained_examples: int = 0,
) -> None:
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO model_state (name, weights_json, bias, trained_examples, updated_at)
            VALUES ('default', ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                weights_json = excluded.weights_json,
                bias = excluded.bias,
                trained_examples = excluded.trained_examples,
                updated_at = excluded.updated_at
            """,
            (json.dumps(weights), bias, trained_examples, now),
        )
        conn.commit()


def prune_jobs(db_path: str, keep_latest: int) -> None:
    keep_latest = int(keep_latest or 0)
    if keep_latest <= 0:
        return
    with _connect(db_path) as conn:
        conn.execute(
            """
            DELETE FROM jobs
            WHERE id NOT IN (
                SELECT id
                FROM jobs
                ORDER BY COALESCE(NULLIF(posted_at, ''), created_at) DESC, id DESC
                LIMIT ?
            )
            """,
            (keep_latest,),
        )
        conn.execute(
            """
            DELETE FROM feedback
            WHERE job_key NOT IN (SELECT job_key FROM jobs)
            """
        )
        conn.commit()


def list_jobs(
    db_path: str,
    statuses: list[str] | None = None,
    easy_apply: bool | None = None,
    platform: str | None = None,
    limit: int = 100,
) -> list[dict]:
    with _connect(db_path) as conn:
        where = []
        params: list = []
        if statuses:
            placeholders = ",".join(["?"] * len(statuses))
            where.append(f"status IN ({placeholders})")
            params.extend(statuses)
        if easy_apply is True:
            where.append("easy_apply = 1")
        if easy_apply is False:
            where.append("(easy_apply = 0 OR easy_apply IS NULL)")
        if platform:
            where.append("platform = ?")
            params.append(platform)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        query = (
            "SELECT "
            "j.job_key, j.platform, j.title, j.company, j.location, j.description, j.job_url, "
            "j.status, j.easy_apply, j.score, j.decision, j.posted_at, j.posted_text, "
            "j.created_at, j.updated_at, j.applied_at, f.label "
            "FROM jobs j "
            "LEFT JOIN feedback f ON f.job_key = j.job_key "
            f"{where_sql.replace('platform = ?', 'j.platform = ?').replace('status IN', 'j.status IN')} "
            "ORDER BY COALESCE(NULLIF(j.posted_at, ''), j.created_at) DESC LIMIT ?"
        )
        params.append(limit)
        cur = conn.execute(query, params)
        rows = cur.fetchall()

    jobs = []
    for row in rows:
        jobs.append(
            {
                "job_key": row[0],
                "platform": row[1],
                "title": row[2],
                "company": row[3],
                "location": row[4],
                "description": row[5],
                "job_url": row[6],
                "status": row[7],
                "easy_apply": row[8],
                "score": row[9],
                "decision": row[10],
                "posted_at": row[11],
                "posted_text": row[12],
                "created_at": row[13],
                "updated_at": row[14],
                "applied_at": row[15],
                "feedback_label": row[16],
            }
        )
    return jobs

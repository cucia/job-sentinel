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
                score INTEGER,
                decision TEXT,
                created_at TEXT,
                updated_at TEXT,
                applied_at TEXT
            );
            """
        )
        conn.commit()


def has_seen_job(db_path: str, job_key: str) -> bool:
    with _connect(db_path) as conn:
        cur = conn.execute("SELECT 1 FROM jobs WHERE job_key = ? LIMIT 1", (job_key,))
        return cur.fetchone() is not None


def enqueue_job(db_path: str, job: dict) -> None:
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO jobs (
                job_key, platform, title, company, location, description, job_url,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.get("job_key"),
                job.get("platform"),
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("description"),
                job.get("job_url"),
                "queued",
                now,
                now,
            ),
        )
        conn.commit()


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


def record_feedback(_db_path: str, _job_key: str, _label: str, _notes: str = "") -> None:
    return None


def get_feedback_label(_db_path: str, _job_key: str) -> str | None:
    return None


def get_approved_count(_db_path: str) -> int:
    return 0


def get_model_state(_db_path: str) -> dict:
    return {}


def save_model_state(_db_path: str, _weights: dict, _bias: float) -> None:
    return None

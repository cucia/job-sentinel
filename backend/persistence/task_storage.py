import sqlite3
from typing import Optional, List
from datetime import datetime
from backend.runtime.task_model import Task, TaskStatus, TaskResult
from backend.manual_review.review_queue import ManualReviewRecord


class TaskStorage:
    """Persistence layer for runtime tasks, bridging to existing storage."""

    def __init__(self, db_path: str):
        """
        Initialize task storage.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create database connection."""
        return sqlite3.connect(self.db_path, timeout=30)

    def _init_schema(self) -> None:
        """Initialize database schema for runtime tasks."""
        with self._connect() as conn:
            # Tasks table (extends existing jobs table)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    source_platform TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    worker_id TEXT,
                    result TEXT,
                    error_message TEXT,
                    manual_review_context TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT
                )
                """
            )

            # Manual review records table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS manual_review_records (
                    task_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    source_platform TEXT NOT NULL,
                    status TEXT NOT NULL,
                    context TEXT,
                    error_message TEXT,
                    reviewer_notes TEXT,
                    reviewer_decision TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    reviewed_at TEXT
                )
                """
            )

            # Task history for audit trail
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    from_status TEXT,
                    to_status TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
                """
            )

            conn.commit()

    def save_task(self, task: Task) -> None:
        """
        Save task to database.

        Args:
            task: Task to save
        """
        import json

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, job_id, source_platform, status, priority, retry_count,
                    max_retries, worker_id, result, error_message, manual_review_context,
                    metadata, created_at, updated_at, started_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status = excluded.status,
                    priority = excluded.priority,
                    retry_count = excluded.retry_count,
                    worker_id = excluded.worker_id,
                    result = excluded.result,
                    error_message = excluded.error_message,
                    manual_review_context = excluded.manual_review_context,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at,
                    started_at = excluded.started_at,
                    completed_at = excluded.completed_at
                """,
                (
                    task.task_id,
                    task.job_id,
                    task.source_platform,
                    task.status.value,
                    task.priority,
                    task.retry_count,
                    task.max_retries,
                    task.worker_id,
                    task.result.value if task.result else None,
                    task.error_message,
                    json.dumps(task.manual_review_context) if task.manual_review_context else None,
                    json.dumps(task.metadata),
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                ),
            )
            conn.commit()

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Retrieve task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task or None if not found
        """
        import json

        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cur.fetchone()

        if not row:
            return None

        return self._row_to_task(row)

    def get_queued_tasks(self, limit: int = 10, order_by: str = "priority DESC, created_at ASC") -> List[Task]:
        """
        Retrieve queued tasks.

        Args:
            limit: Maximum number of tasks
            order_by: SQL ORDER BY clause

        Returns:
            List of queued tasks
        """
        with self._connect() as conn:
            cur = conn.execute(
                f"SELECT * FROM tasks WHERE status = ? ORDER BY {order_by} LIMIT ?",
                (TaskStatus.QUEUED.value, limit),
            )
            rows = cur.fetchall()

        return [self._row_to_task(row) for row in rows]

    def get_tasks_by_status(self, status: TaskStatus, limit: int = 100) -> List[Task]:
        """
        Retrieve tasks by status.

        Args:
            status: Task status to filter by
            limit: Maximum number of tasks

        Returns:
            List of tasks with given status
        """
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status.value, limit),
            )
            rows = cur.fetchall()

        return [self._row_to_task(row) for row in rows]

    def count_tasks_by_status(self, status: TaskStatus) -> int:
        """
        Count tasks by status.

        Args:
            status: Task status to filter by

        Returns:
            Count of tasks with given status
        """
        with self._connect() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = ?", (status.value,))
            row = cur.fetchone()

        return row[0] if row else 0

    def get_task_history(self, task_id: str) -> List[dict]:
        """
        Retrieve state transition history for task.

        Args:
            task_id: Task identifier

        Returns:
            List of state transitions
        """
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT from_status, to_status, timestamp FROM task_history WHERE task_id = ? ORDER BY timestamp ASC",
                (task_id,),
            )
            rows = cur.fetchall()

        return [
            {
                "from_status": row[0],
                "to_status": row[1],
                "timestamp": row[2],
            }
            for row in rows
        ]

    def record_state_transition(self, task_id: str, from_status: str, to_status: str) -> None:
        """
        Record state transition in history.

        Args:
            task_id: Task identifier
            from_status: Previous status
            to_status: New status
        """
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO task_history (task_id, from_status, to_status, timestamp) VALUES (?, ?, ?, ?)",
                (task_id, from_status, to_status, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def save_manual_review_record(self, record: ManualReviewRecord) -> None:
        """
        Save manual review record.

        Args:
            record: ManualReviewRecord to save
        """
        import json

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO manual_review_records (
                    task_id, job_id, source_platform, status, context, error_message,
                    reviewer_notes, reviewer_decision, created_at, updated_at, reviewed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status = excluded.status,
                    context = excluded.context,
                    error_message = excluded.error_message,
                    reviewer_notes = excluded.reviewer_notes,
                    reviewer_decision = excluded.reviewer_decision,
                    updated_at = excluded.updated_at,
                    reviewed_at = excluded.reviewed_at
                """,
                (
                    record.task_id,
                    record.job_id,
                    record.source_platform,
                    record.status,
                    json.dumps(record.context) if record.context else None,
                    record.error_message,
                    record.reviewer_notes,
                    record.reviewer_decision,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                    record.reviewed_at.isoformat() if record.reviewed_at else None,
                ),
            )
            conn.commit()

    def get_manual_review_record(self, task_id: str) -> Optional[ManualReviewRecord]:
        """
        Retrieve manual review record by task ID.

        Args:
            task_id: Task identifier

        Returns:
            ManualReviewRecord or None if not found
        """
        import json

        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM manual_review_records WHERE task_id = ?", (task_id,))
            row = cur.fetchone()

        if not row:
            return None

        return ManualReviewRecord(
            task_id=row[0],
            job_id=row[1],
            source_platform=row[2],
            status=row[3],
            context=json.loads(row[4]) if row[4] else {},
            error_message=row[5],
            reviewer_notes=row[6],
            reviewer_decision=row[7],
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9]),
            reviewed_at=datetime.fromisoformat(row[10]) if row[10] else None,
        )

    def get_manual_review_records(
        self,
        status: str = "pending",
        platform: str = None,
        limit: int = 100,
    ) -> List[ManualReviewRecord]:
        """
        Retrieve manual review records.

        Args:
            status: Filter by status
            platform: Filter by platform
            limit: Maximum number of records

        Returns:
            List of ManualReviewRecords
        """
        import json

        where_clauses = ["status = ?"]
        params = [status]

        if platform:
            where_clauses.append("source_platform = ?")
            params.append(platform)

        where_sql = " AND ".join(where_clauses)

        with self._connect() as conn:
            cur = conn.execute(
                f"SELECT * FROM manual_review_records WHERE {where_sql} ORDER BY created_at DESC LIMIT ?",
                params + [limit],
            )
            rows = cur.fetchall()

        records = []
        for row in rows:
            records.append(
                ManualReviewRecord(
                    task_id=row[0],
                    job_id=row[1],
                    source_platform=row[2],
                    status=row[3],
                    context=json.loads(row[4]) if row[4] else {},
                    error_message=row[5],
                    reviewer_notes=row[6],
                    reviewer_decision=row[7],
                    created_at=datetime.fromisoformat(row[8]),
                    updated_at=datetime.fromisoformat(row[9]),
                    reviewed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                )
            )

        return records

    def count_manual_review_records(self, status: str = "pending", platform: str = None) -> int:
        """
        Count manual review records.

        Args:
            status: Filter by status
            platform: Filter by platform

        Returns:
            Count of records
        """
        where_clauses = ["status = ?"]
        params = [status]

        if platform:
            where_clauses.append("source_platform = ?")
            params.append(platform)

        where_sql = " AND ".join(where_clauses)

        with self._connect() as conn:
            cur = conn.execute(f"SELECT COUNT(*) FROM manual_review_records WHERE {where_sql}", params)
            row = cur.fetchone()

        return row[0] if row else 0

    @staticmethod
    def _row_to_task(row: tuple) -> Task:
        """Convert database row to Task object."""
        import json

        return Task(
            task_id=row[0],
            job_id=row[1],
            source_platform=row[2],
            status=TaskStatus(row[3]),
            priority=row[4],
            retry_count=row[5],
            max_retries=row[6],
            worker_id=row[7],
            result=TaskResult(row[8]) if row[8] else None,
            error_message=row[9],
            manual_review_context=json.loads(row[10]) if row[10] else None,
            metadata=json.loads(row[11]) if row[11] else {},
            created_at=datetime.fromisoformat(row[12]),
            updated_at=datetime.fromisoformat(row[13]),
            started_at=datetime.fromisoformat(row[14]) if row[14] else None,
            completed_at=datetime.fromisoformat(row[15]) if row[15] else None,
        )

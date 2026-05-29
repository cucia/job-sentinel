from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from backend.runtime.task_model import Task


@dataclass
class ManualReviewRecord:
    """Record for manual review escalation."""
    task_id: str
    job_id: str
    source_platform: str
    status: str = "pending"
    context: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    reviewer_decision: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "job_id": self.job_id,
            "source_platform": self.source_platform,
            "status": self.status,
            "context": self.context,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewer_notes": self.reviewer_notes,
            "reviewer_decision": self.reviewer_decision,
        }

    @staticmethod
    def from_task(task: Task) -> "ManualReviewRecord":
        """Create review record from task."""
        return ManualReviewRecord(
            task_id=task.task_id,
            job_id=task.job_id,
            source_platform=task.source_platform,
            context=task.manual_review_context or {},
            error_message=task.error_message,
        )


class ManualReviewQueue:
    """Queue for tasks requiring manual review."""

    def __init__(self, storage):
        """
        Initialize manual review queue.

        Args:
            storage: Storage layer for persistence
        """
        self.storage = storage

    def enqueue(self, task: Task, context: dict) -> ManualReviewRecord:
        """
        Add task to manual review queue.

        Args:
            task: Task requiring review
            context: Review context (state, error, etc.)

        Returns:
            ManualReviewRecord
        """
        record = ManualReviewRecord.from_task(task)
        record.context = context
        self.storage.save_manual_review_record(record)
        return record

    def get_pending(self, limit: int = 100) -> List[ManualReviewRecord]:
        """
        Retrieve pending review records.

        Args:
            limit: Maximum number of records

        Returns:
            List of pending review records
        """
        return self.storage.get_manual_review_records(status="pending", limit=limit)

    def get_record(self, task_id: str) -> Optional[ManualReviewRecord]:
        """
        Retrieve review record by task ID.

        Args:
            task_id: Task identifier

        Returns:
            ManualReviewRecord or None if not found
        """
        return self.storage.get_manual_review_record(task_id)

    def mark_reviewed(
        self,
        task_id: str,
        decision: str,
        notes: str = "",
    ) -> ManualReviewRecord:
        """
        Mark review record as reviewed.

        Args:
            task_id: Task identifier
            decision: Reviewer decision (approve, reject, defer)
            notes: Reviewer notes

        Returns:
            Updated ManualReviewRecord
        """
        record = self.storage.get_manual_review_record(task_id)
        if not record:
            raise ValueError(f"Review record not found for task {task_id}")
        record.status = "reviewed"
        record.reviewed_at = datetime.utcnow()
        record.reviewer_decision = decision
        record.reviewer_notes = notes
        record.updated_at = datetime.utcnow()
        self.storage.save_manual_review_record(record)
        return record

    def get_review_stats(self) -> dict:
        """
        Get manual review queue statistics.

        Returns:
            Stats dict with pending, reviewed counts
        """
        pending = self.storage.count_manual_review_records(status="pending")
        reviewed = self.storage.count_manual_review_records(status="reviewed")
        return {
            "pending": pending,
            "reviewed": reviewed,
            "total": pending + reviewed,
        }

    def get_records_by_platform(self, platform: str, status: str = "pending") -> List[ManualReviewRecord]:
        """
        Retrieve review records by platform.

        Args:
            platform: Source platform
            status: Filter by status

        Returns:
            List of review records
        """
        return self.storage.get_manual_review_records(
            platform=platform,
            status=status,
        )

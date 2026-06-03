from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class TaskStatus(str, Enum):
    """Task lifecycle states."""
    DISCOVERED = "discovered"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    MANUAL_REVIEW = "manual_review"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskResult(str, Enum):
    """Task execution outcomes."""
    APPLIED = "applied"
    REVIEW = "review"
    SKIPPED = "skipped"
    DEFERRED = "deferred"
    FAILED = "failed"


@dataclass
class Task:
    """Canonical runtime task model."""
    task_id: str
    job_id: str
    source_platform: str
    status: TaskStatus
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    result: Optional[TaskResult] = None
    error_message: Optional[str] = None
    manual_review_context: Optional[dict] = None
    metadata: dict = field(default_factory=dict)
    # Workflow classification fields
    workflow_type: Optional[str] = None
    execution_strategy: Optional[str] = None
    workflow_confidence: float = 0.0
    workflow_indicators: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert task to dictionary, serializing enums and datetimes."""
        data = asdict(self)
        data["status"] = self.status.value
        if self.result:
            data["result"] = self.result.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data

    @staticmethod
    def from_dict(data: dict) -> "Task":
        """Reconstruct task from dictionary."""
        data = dict(data)
        data["status"] = TaskStatus(data["status"])
        if data.get("result"):
            data["result"] = TaskResult(data["result"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return Task(**data)

    def is_retryable(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED

    def can_start(self) -> bool:
        """Check if task is ready to start."""
        return self.status == TaskStatus.QUEUED

    def mark_running(self, worker_id: str) -> None:
        """Transition task to running state."""
        if self.status != TaskStatus.QUEUED:
            raise ValueError(f"Cannot start task in {self.status} state")
        self.status = TaskStatus.RUNNING
        self.worker_id = worker_id
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_completed(self, result: TaskResult) -> None:
        """Transition task to completed state."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in {self.status} state")
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Transition task to failed state."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot fail task in {self.status} state")
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_manual_review(self, context: dict) -> None:
        """Escalate task to manual review."""
        self.status = TaskStatus.MANUAL_REVIEW
        self.manual_review_context = context
        self.updated_at = datetime.utcnow()

    def retry(self) -> None:
        """Prepare task for retry."""
        if not self.is_retryable():
            raise ValueError(f"Task cannot be retried (retries: {self.retry_count}/{self.max_retries})")
        self.retry_count += 1
        self.status = TaskStatus.QUEUED
        self.worker_id = None
        self.started_at = None
        self.error_message = None
        self.updated_at = datetime.utcnow()

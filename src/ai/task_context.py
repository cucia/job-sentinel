"""
Task Context for Multi-Agent Coordination

Shared state object passed between agents during job application flow.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    DELEGATED = "delegated"


class AgentType(Enum):
    """Types of agents in the system."""
    EVALUATOR = "evaluator"
    NAVIGATOR = "navigator"
    FORM_DETECTOR = "form_detector"
    FORM_FILLER = "form_filler"
    APPLICATION = "application"
    RECOVERY = "recovery"
    REVIEW = "review"


@dataclass
class AgentAttempt:
    """Record of an agent's attempt to handle the task."""
    agent_type: str
    timestamp: str
    action: str
    result: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormField:
    """Detected form field information."""
    field_type: str  # text, email, select, file, etc.
    name: str
    label: str
    required: bool
    selector: str
    options: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    """
    Shared context passed between agents during job application.

    This object tracks the entire application flow from evaluation
    to submission, including all agent interactions and state changes.
    """

    # Job identification
    job_id: str
    job_key: str
    platform: str

    # URLs and navigation
    source_url: str
    apply_url: Optional[str] = None
    company_url: Optional[str] = None
    current_url: Optional[str] = None

    # Task state
    status: TaskStatus = TaskStatus.PENDING
    current_agent: Optional[str] = None

    # Detection flags
    form_detected: bool = False
    auth_required: bool = False
    captcha_detected: bool = False
    external_redirect: bool = False
    easy_apply_available: bool = False

    # Form information
    detected_fields: List[FormField] = field(default_factory=list)
    filled_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)

    # Execution tracking
    attempts: List[AgentAttempt] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2

    # Results
    submission_successful: bool = False
    confirmation_message: Optional[str] = None

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_attempt(self, agent_type: AgentType, action: str, result: str,
                    error: Optional[str] = None, **metadata) -> None:
        """Record an agent's attempt."""
        attempt = AgentAttempt(
            agent_type=agent_type.value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            result=result,
            error=error,
            metadata=metadata
        )
        self.attempts.append(attempt)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_error(self, error: str) -> None:
        """Add an error to the error log."""
        self.errors.append(f"[{datetime.now(timezone.utc).isoformat()}] {error}")
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_status(self, status: TaskStatus, agent: Optional[str] = None) -> None:
        """Update task status."""
        self.status = status
        if agent:
            self.current_agent = agent
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "job_id": self.job_id,
            "job_key": self.job_key,
            "platform": self.platform,
            "source_url": self.source_url,
            "apply_url": self.apply_url,
            "company_url": self.company_url,
            "current_url": self.current_url,
            "status": self.status.value,
            "current_agent": self.current_agent,
            "form_detected": self.form_detected,
            "auth_required": self.auth_required,
            "captcha_detected": self.captcha_detected,
            "external_redirect": self.external_redirect,
            "easy_apply_available": self.easy_apply_available,
            "detected_fields": [
                {
                    "type": f.field_type,
                    "name": f.name,
                    "label": f.label,
                    "required": f.required,
                    "selector": f.selector,
                    "options": f.options
                }
                for f in self.detected_fields
            ],
            "filled_fields": self.filled_fields,
            "missing_fields": self.missing_fields,
            "attempts": [
                {
                    "agent": a.agent_type,
                    "timestamp": a.timestamp,
                    "action": a.action,
                    "result": a.result,
                    "error": a.error,
                    "metadata": a.metadata
                }
                for a in self.attempts
            ],
            "errors": self.errors,
            "retry_count": self.retry_count,
            "submission_successful": self.submission_successful,
            "confirmation_message": self.confirmation_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }


def create_task_context(job: dict, platform: str) -> TaskContext:
    """
    Factory function to create TaskContext from job dict.

    Args:
        job: Job dictionary with job details
        platform: Platform name (linkedin, indeed, etc.)

    Returns:
        Initialized TaskContext
    """
    return TaskContext(
        job_id=job.get("id", ""),
        job_key=job.get("job_key", ""),
        platform=platform,
        source_url=job.get("job_url", ""),
        apply_url=job.get("apply_url"),
        easy_apply_available=job.get("easy_apply", False),
        metadata={
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
        }
    )

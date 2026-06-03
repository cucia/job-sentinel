"""
Application Session Model

Tracks application progress, session state, and discovered information.
Persistable and recoverable for long-running application workflows.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class SessionStatus(str, Enum):
    """Application session lifecycle states."""
    INITIALIZED = "initialized"
    PAGE_LOADING = "page_loading"
    PAGE_ANALYZED = "page_analyzed"
    PLANNING = "planning"
    READY_TO_EXECUTE = "ready_to_execute"
    EXECUTING = "executing"
    AWAITING_INPUT = "awaiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"


class ExecutionAction(str, Enum):
    """Actions that can be planned or executed."""
    UPLOAD_RESUME = "upload_resume"
    UPLOAD_DOCUMENTS = "upload_documents"
    FILL_PROFILE = "fill_profile"
    ANSWER_QUESTIONS = "answer_questions"
    SELECT_OPTIONS = "select_options"
    CONTINUE_TO_NEXT_STEP = "continue_to_next_step"
    SUBMIT_APPLICATION = "submit_application"
    CONFIRM_APPLICATION = "confirm_application"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    VERIFY_SUBMISSION = "verify_submission"


@dataclass
class PageElement:
    """Structured representation of a page element."""
    element_id: str
    element_type: str  # "input", "button", "select", "textarea", etc.
    label: Optional[str] = None
    name: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    visible: bool = True
    value: Optional[str] = None
    options: list = field(default_factory=list)  # For select/radio/checkbox
    validation_rules: dict = field(default_factory=dict)


@dataclass
class PageForm:
    """Structured representation of a form on a page."""
    form_id: str
    form_name: Optional[str] = None
    form_type: str = "unknown"  # "profile", "questions", "upload", etc.
    elements: list[PageElement] = field(default_factory=list)
    submit_button: Optional[PageElement] = None
    required_fields: list[str] = field(default_factory=list)


@dataclass
class PageAnalysisResult:
    """Result of analyzing a page structure."""
    page_type: str  # "job_posting", "application_form", "profile", "questions", etc.
    url: str
    title: Optional[str] = None
    forms: list[PageForm] = field(default_factory=list)
    visible_fields: list[str] = field(default_factory=list)
    upload_fields: list[str] = field(default_factory=list)
    buttons: list[PageElement] = field(default_factory=list)
    navigation_actions: list[str] = field(default_factory=list)
    validation_messages: list[str] = field(default_factory=list)
    estimated_completion: float = 0.0  # percentage
    next_action_hint: Optional[str] = None
    accessibility_notes: list[str] = field(default_factory=list)


@dataclass
class ExecutionPlanStep:
    """Single step in an execution plan."""
    step_number: int
    action: ExecutionAction
    description: str
    required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)
    estimated_duration_seconds: int = 30
    fallback_action: Optional[ExecutionAction] = None
    validation_checks: list[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """Workflow-specific execution plan."""
    plan_id: str
    workflow_type: str
    job_id: str
    task_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    steps: list[ExecutionPlanStep] = field(default_factory=list)
    total_estimated_duration: int = 0
    confidence_score: float = 0.0
    requires_manual_review: bool = False
    review_reasons: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)


@dataclass
class ApplicationSession:
    """
    Persistent session tracking application progress.

    Tracks job application workflow from discovery through completion.
    Recoverable and resumable for interrupted workflows.
    """
    session_id: str
    job_id: str
    task_id: str
    workflow_type: str  # "linkedin", "indeed", "naukri", etc.
    current_url: str
    current_step: str = "initialized"
    status: SessionStatus = SessionStatus.INITIALIZED

    # Timeline
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # State tracking
    session_state: dict = field(default_factory=dict)  # Arbitrary workflow state

    # Discovery
    discovered_fields: dict = field(default_factory=dict)  # Fields found on pages
    discovered_forms: dict = field(default_factory=dict)  # Forms found on pages
    discovered_pages: list[dict] = field(default_factory=list)  # Page sequence

    # Document tracking
    uploaded_documents: list[dict] = field(default_factory=list)  # {type, filename, url}

    # Execution tracking
    execution_history: list[dict] = field(default_factory=list)  # {timestamp, action, result}
    execution_plan: Optional[ExecutionPlan] = None
    current_plan_step: int = 0

    # Analysis results
    page_analyses: list[PageAnalysisResult] = field(default_factory=list)

    # Error tracking
    errors: list[dict] = field(default_factory=list)  # {timestamp, error_type, message}
    retry_count: int = 0
    max_retries: int = 3

    # Metadata
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert session to dictionary for persistence."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        data["status"] = self.status.value
        if self.execution_plan:
            data["execution_plan"] = asdict(self.execution_plan)
        return data

    @staticmethod
    def from_dict(d: dict) -> "ApplicationSession":
        """Restore session from dictionary."""
        # Parse dates
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d["updated_at"] = datetime.fromisoformat(d["updated_at"])
        if d.get("completed_at"):
            d["completed_at"] = datetime.fromisoformat(d["completed_at"])

        # Parse status
        if isinstance(d.get("status"), str):
            d["status"] = SessionStatus(d["status"])

        # Parse execution plan if present
        if d.get("execution_plan"):
            plan_data = d["execution_plan"]
            plan_data["created_at"] = datetime.fromisoformat(plan_data["created_at"])
            d["execution_plan"] = ExecutionPlan(**plan_data)

        return ApplicationSession(**d)

    def record_page_analysis(self, analysis: PageAnalysisResult) -> None:
        """Record page analysis result."""
        self.page_analyses.append(analysis)
        self.updated_at = datetime.utcnow()
        self.discovered_fields.update({f: True for f in analysis.visible_fields})
        self.current_url = analysis.url

    def record_execution_step(self, action: ExecutionAction, result: dict) -> None:
        """Record execution step."""
        self.execution_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action.value,
            "result": result,
        })
        self.updated_at = datetime.utcnow()

    def record_error(self, error_type: str, message: str) -> None:
        """Record error."""
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "message": message,
        })
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def set_execution_plan(self, plan: ExecutionPlan) -> None:
        """Set the execution plan."""
        self.execution_plan = plan
        self.status = SessionStatus.READY_TO_EXECUTE
        self.updated_at = datetime.utcnow()

    def complete(self, success: bool = True) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

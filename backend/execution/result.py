"""
Execution Result

Dataclass representing the outcome of executing an ExecutionPlan.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ExecutionResult:
    """Result of executing an ExecutionPlan."""

    success: bool
    """Whether execution succeeded overall"""

    status: str
    """Current status: pending, in_progress, completed, failed, partial"""

    completed_steps: int
    """Number of successfully completed steps"""

    failed_step: Optional[int] = None
    """Step number that failed, or None if all succeeded"""

    errors: List[str] = field(default_factory=list)
    """List of error messages encountered"""

    execution_time: float = 0.0
    """Total execution time in seconds"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional execution metadata"""

    execution_plan_id: Optional[str] = None
    """ID of the ExecutionPlan that was executed"""

    started_at: Optional[datetime] = None
    """Timestamp when execution started"""

    completed_at: Optional[datetime] = None
    """Timestamp when execution completed"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "status": self.status,
            "completed_steps": self.completed_steps,
            "failed_step": self.failed_step,
            "errors": self.errors,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "execution_plan_id": self.execution_plan_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

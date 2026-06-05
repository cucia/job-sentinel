"""
State Tracker

Tracks execution state during plan execution.
Records current step, completed steps, failed steps, and timestamps.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class StateTracker:
    """Tracks execution state during plan execution."""

    def __init__(self, plan_id: str, total_steps: int):
        """
        Initialize state tracker.

        Args:
            plan_id: ID of the ExecutionPlan being tracked
            total_steps: Total number of steps in plan
        """
        self.plan_id = plan_id
        self.total_steps = total_steps
        self.current_step = 0
        self.completed_steps = []
        self.failed_steps = []
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.step_history = []

    def start_execution(self):
        """Mark execution as started."""
        self.status = "in_progress"
        self.start_time = datetime.utcnow()

    def complete_step(self, step_number: int, step_name: str, duration: float, metadata: Dict[str, Any] = None):
        """
        Record step completion.

        Args:
            step_number: Step number (1-indexed)
            step_name: Name/description of step
            duration: How long step took in seconds
            metadata: Optional additional metadata
        """
        if step_number not in self.completed_steps:
            self.completed_steps.append(step_number)

        self.current_step = step_number
        self.step_history.append({
            "step": step_number,
            "name": step_name,
            "status": "completed",
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        })

    def fail_step(self, step_number: int, step_name: str, error: str, metadata: Dict[str, Any] = None):
        """
        Record step failure.

        Args:
            step_number: Step number (1-indexed)
            step_name: Name/description of step
            error: Error message
            metadata: Optional additional metadata
        """
        if step_number not in self.failed_steps:
            self.failed_steps.append(step_number)

        self.current_step = step_number
        self.status = "failed"
        self.step_history.append({
            "step": step_number,
            "name": step_name,
            "status": "failed",
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        })

    def finish_execution(self, success: bool):
        """
        Mark execution as finished.

        Args:
            success: Whether execution succeeded overall
        """
        self.end_time = datetime.utcnow()
        self.status = "completed" if success else "failed"

    def get_execution_time(self) -> float:
        """Get total execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def get_state(self) -> Dict[str, Any]:
        """Get current state as dictionary."""
        return {
            "plan_id": self.plan_id,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.get_execution_time(),
            "step_history": self.step_history,
        }

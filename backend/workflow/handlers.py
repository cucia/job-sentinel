"""
Workflow Routing Handlers

Lightweight handlers for workflow-aware routing.
No execution logic - only task routing and preparation.

Supported workflows:
- LinkedIn Easy Apply
- Workday
- Greenhouse
- Lever
- Oracle
- Generic
"""

from abc import ABC, abstractmethod
from backend.runtime.task_model import Task
from src.core.logger import log


class WorkflowHandler(ABC):
    """Base class for workflow handlers."""

    def __init__(self, workflow_type: str):
        """
        Initialize handler.

        Args:
            workflow_type: Type of workflow this handler manages
        """
        self.workflow_type = workflow_type

    @abstractmethod
    def can_handle(self, task: Task) -> bool:
        """
        Check if handler can process this task.

        Args:
            task: Task to evaluate

        Returns:
            True if handler can process, False otherwise
        """
        pass

    @abstractmethod
    def prepare_for_processing(self, task: Task) -> dict:
        """
        Prepare task for workflow-specific processing.

        Args:
            task: Task to prepare

        Returns:
            Dict with preparation results and next steps
        """
        pass

    def validate_workflow_assignment(self, task: Task) -> tuple[bool, str]:
        """
        Validate that task is correctly assigned to this workflow.

        Args:
            task: Task to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        if task.workflow_type != self.workflow_type:
            return False, f"Workflow mismatch: {task.workflow_type} != {self.workflow_type}"

        if not task.execution_strategy:
            return False, "No execution strategy attached to task"

        return True, "Valid"


class LinkedInEasyApplyHandler(WorkflowHandler):
    """Handler for LinkedIn Easy Apply workflow."""

    def __init__(self):
        """Initialize LinkedIn Easy Apply handler."""
        super().__init__("linkedin_easy_apply")

    def can_handle(self, task: Task) -> bool:
        """Check if task is LinkedIn Easy Apply."""
        return task.workflow_type == "linkedin_easy_apply"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare LinkedIn task for processing."""
        is_valid, reason = self.validate_workflow_assignment(task)

        if not is_valid:
            return {
                "valid": False,
                "reason": reason,
                "workflow": self.workflow_type,
            }

        log(f"[LinkedIn Handler] Preparing task {task.task_id} for Easy Apply")
        log(f"  - Confidence: {task.workflow_confidence:.0%}")
        log(f"  - Strategy: {task.execution_strategy}")

        return {
            "valid": True,
            "workflow": self.workflow_type,
            "execution_strategy": task.execution_strategy,
            "confidence": task.workflow_confidence,
            "next_step": "apply_via_easy_apply",
            "requires": ["linkedin_session", "resume"],
        }


class WorkdayHandler(WorkflowHandler):
    """Handler for Workday workflow."""

    def __init__(self):
        """Initialize Workday handler."""
        super().__init__("workday")

    def can_handle(self, task: Task) -> bool:
        """Check if task is Workday."""
        return task.workflow_type == "workday"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare Workday task for processing."""
        is_valid, reason = self.validate_workflow_assignment(task)

        if not is_valid:
            return {
                "valid": False,
                "reason": reason,
                "workflow": self.workflow_type,
            }

        log(f"[Workday Handler] Preparing task {task.task_id} for Workday form")
        log(f"  - Confidence: {task.workflow_confidence:.0%}")
        log(f"  - Strategy: {task.execution_strategy}")

        return {
            "valid": True,
            "workflow": self.workflow_type,
            "execution_strategy": task.execution_strategy,
            "confidence": task.workflow_confidence,
            "next_step": "fill_workday_form",
            "requires": ["form_parser", "resume", "profile_data"],
        }


class GreenhouseHandler(WorkflowHandler):
    """Handler for Greenhouse workflow."""

    def __init__(self):
        """Initialize Greenhouse handler."""
        super().__init__("greenhouse")

    def can_handle(self, task: Task) -> bool:
        """Check if task is Greenhouse."""
        return task.workflow_type == "greenhouse"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare Greenhouse task for processing."""
        is_valid, reason = self.validate_workflow_assignment(task)

        if not is_valid:
            return {
                "valid": False,
                "reason": reason,
                "workflow": self.workflow_type,
            }

        log(f"[Greenhouse Handler] Preparing task {task.task_id} for Greenhouse")
        log(f"  - Confidence: {task.workflow_confidence:.0%}")
        log(f"  - Strategy: {task.execution_strategy}")

        return {
            "valid": True,
            "workflow": self.workflow_type,
            "execution_strategy": task.execution_strategy,
            "confidence": task.workflow_confidence,
            "next_step": "apply_via_greenhouse",
            "requires": ["form_parser", "resume"],
        }


class LeverHandler(WorkflowHandler):
    """Handler for Lever workflow."""

    def __init__(self):
        """Initialize Lever handler."""
        super().__init__("lever")

    def can_handle(self, task: Task) -> bool:
        """Check if task is Lever."""
        return task.workflow_type == "lever"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare Lever task for processing."""
        is_valid, reason = self.validate_workflow_assignment(task)

        if not is_valid:
            return {
                "valid": False,
                "reason": reason,
                "workflow": self.workflow_type,
            }

        log(f"[Lever Handler] Preparing task {task.task_id} for Lever")
        log(f"  - Confidence: {task.workflow_confidence:.0%}")
        log(f"  - Strategy: {task.execution_strategy}")

        return {
            "valid": True,
            "workflow": self.workflow_type,
            "execution_strategy": task.execution_strategy,
            "confidence": task.workflow_confidence,
            "next_step": "apply_via_lever",
            "requires": ["form_parser", "resume"],
        }


class OracleHandler(WorkflowHandler):
    """Handler for Oracle workflow."""

    def __init__(self):
        """Initialize Oracle handler."""
        super().__init__("oracle")

    def can_handle(self, task: Task) -> bool:
        """Check if task is Oracle."""
        return task.workflow_type == "oracle"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare Oracle task for processing."""
        is_valid, reason = self.validate_workflow_assignment(task)

        if not is_valid:
            return {
                "valid": False,
                "reason": reason,
                "workflow": self.workflow_type,
            }

        log(f"[Oracle Handler] Preparing task {task.task_id} for Oracle")
        log(f"  - Confidence: {task.workflow_confidence:.0%}")
        log(f"  - Strategy: {task.execution_strategy}")

        return {
            "valid": True,
            "workflow": self.workflow_type,
            "execution_strategy": task.execution_strategy,
            "confidence": task.workflow_confidence,
            "next_step": "apply_via_oracle",
            "requires": ["form_parser", "resume", "profile_data"],
        }


class GenericHandler(WorkflowHandler):
    """Handler for Generic/Unknown workflow."""

    def __init__(self):
        """Initialize Generic handler."""
        super().__init__("generic")

    def can_handle(self, task: Task) -> bool:
        """Check if task is generic."""
        return task.workflow_type == "generic"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare generic task for processing."""
        is_valid, reason = self.validate_workflow_assignment(task)

        if not is_valid:
            return {
                "valid": False,
                "reason": reason,
                "workflow": self.workflow_type,
            }

        log(f"[Generic Handler] Preparing task {task.task_id} for generic form")
        log(f"  - Confidence: {task.workflow_confidence:.0%}")
        log(f"  - Strategy: {task.execution_strategy}")

        return {
            "valid": True,
            "workflow": self.workflow_type,
            "execution_strategy": task.execution_strategy,
            "confidence": task.workflow_confidence,
            "next_step": "apply_via_generic_form",
            "requires": ["form_parser", "resume"],
        }


class WorkflowHandlerRegistry:
    """Registry of workflow handlers for routing."""

    def __init__(self):
        """Initialize handler registry with all supported workflows."""
        self.handlers = {
            "linkedin_easy_apply": LinkedInEasyApplyHandler(),
            "workday": WorkdayHandler(),
            "greenhouse": GreenhouseHandler(),
            "lever": LeverHandler(),
            "oracle": OracleHandler(),
            "generic": GenericHandler(),
        }

    def get_handler(self, workflow_type: str) -> WorkflowHandler:
        """
        Get handler for workflow type.

        Args:
            workflow_type: Type of workflow

        Returns:
            Handler for workflow type or generic handler
        """
        handler = self.handlers.get(workflow_type)
        if handler:
            return handler

        log(f"[Registry] Unknown workflow type: {workflow_type}, using generic")
        return self.handlers["generic"]

    def route_task(self, task: Task) -> dict:
        """
        Route task to appropriate handler.

        Args:
            task: Task to route

        Returns:
            Dict with routing result and preparation data
        """
        handler = self.get_handler(task.workflow_type or "generic")

        if not handler.can_handle(task):
            return {
                "valid": False,
                "reason": f"Handler cannot process {task.workflow_type}",
                "workflow": task.workflow_type,
            }

        result = handler.prepare_for_processing(task)
        result["handler"] = handler.__class__.__name__

        return result

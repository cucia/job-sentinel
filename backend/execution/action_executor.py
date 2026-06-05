"""
Action Executor

Translates ExecutionPlanStep objects into BrowserAdapter operations.
Bridges execution planning and browser automation.

Supports:
- FILL_PROFILE: Fill form fields
- UPLOAD_RESUME: Upload files
- SUBMIT_APPLICATION: Click submit buttons
- CONTINUE_TO_NEXT_STEP: Navigate to next page
- CONFIRM_APPLICATION: User confirmation
- VERIFY_SUBMISSION: Check submission status
"""

from typing import Optional, Dict, Any
from datetime import datetime
from backend.application.session import ExecutionPlanStep, ExecutionAction, ApplicationSession
from backend.browser.adapter import BrowserAdapter
from backend.browser.result import BrowserResult
from src.core.logger import log


class ActionExecutionResult:
    """Result of executing a single action."""

    def __init__(
        self,
        success: bool,
        action: str,
        step_number: int,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize result.

        Args:
            success: Whether action succeeded
            action: Action performed
            step_number: Step number
            message: Result message
            metadata: Additional metadata
        """
        self.success = success
        self.action = action
        self.step_number = step_number
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "action": self.action,
            "step_number": self.step_number,
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "✓" if self.success else "✗"
        return f"{status} Step {self.step_number} ({self.action}): {self.message}"


class ActionExecutor:
    """Executes ExecutionPlanStep actions using BrowserAdapter."""

    def __init__(self, browser_adapter: BrowserAdapter):
        """
        Initialize action executor.

        Args:
            browser_adapter: BrowserAdapter instance for browser operations
        """
        self.adapter = browser_adapter

        # Action handlers
        self.action_handlers = {
            ExecutionAction.FILL_PROFILE: self.execute_fill,
            ExecutionAction.UPLOAD_RESUME: self.execute_upload,
            ExecutionAction.UPLOAD_DOCUMENTS: self.execute_upload,
            ExecutionAction.SUBMIT_APPLICATION: self.execute_click,
            ExecutionAction.CONTINUE_TO_NEXT_STEP: self.execute_click,
            ExecutionAction.CONFIRM_APPLICATION: self.execute_confirm,
            ExecutionAction.VERIFY_SUBMISSION: self.execute_validation,
            ExecutionAction.ANSWER_QUESTIONS: self.execute_fill,
            ExecutionAction.SELECT_OPTIONS: self.execute_select,
        }

    async def execute_step(
        self,
        step: ExecutionPlanStep,
        session: ApplicationSession,
    ) -> ActionExecutionResult:
        """
        Execute a single execution plan step.

        Args:
            step: ExecutionPlanStep to execute
            session: ApplicationSession context

        Returns:
            ActionExecutionResult with outcome
        """
        log(f"[ActionExecutor] Executing step {step.step_number}: {step.action}")

        # Validate step
        if not step.action:
            return ActionExecutionResult(
                success=False,
                action="unknown",
                step_number=step.step_number,
                message="Step has no action defined",
            )

        # Get handler for this action
        handler = self.action_handlers.get(step.action)

        if not handler:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message=f"No handler for action: {step.action}",
            )

        # Execute action
        try:
            result = await handler(step, session)
            log(f"[ActionExecutor] {result}")
            return result
        except Exception as e:
            log(f"[ActionExecutor] Exception: {e}")
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message=f"Exception: {str(e)}",
                metadata={"error_type": type(e).__name__},
            )

    async def execute_fill(
        self,
        step: ExecutionPlanStep,
        session: ApplicationSession,
    ) -> ActionExecutionResult:
        """
        Execute FILL_PROFILE or ANSWER_QUESTIONS action.

        Args:
            step: ExecutionPlanStep with fill action
            session: ApplicationSession context

        Returns:
            ActionExecutionResult
        """
        if not step.selector:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message="No selector provided for fill action",
            )

        try:
            # Find element
            element = await self.adapter.find_element(step.selector)
            if not element:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=f"Element not found: {step.selector}",
                    metadata={"selector": step.selector},
                )

            # Get value
            value = step.expected_value or ""
            if step.value_source == "user_profile":
                value = await self._resolve_value_from_profile(
                    step.field_name or "", session
                )
            elif step.value_source == "ai_generated":
                value = f"[AI-generated response for {step.field_name}]"
            elif step.value_source == "profile":
                value = await self._resolve_value_from_metadata(step, session)

            # Detect element type and handle accordingly
            element_type = await element.get_attribute("type")

            if element_type and element_type.lower() == "checkbox":
                # Handle checkbox: check or uncheck based on value
                should_check = value.lower() in ("true", "1", "yes", "on", "checked")

                if should_check:
                    result = await element.check()
                else:
                    result = await element.uncheck()
            else:
                # Handle regular input/textarea (await async operation)
                result = await element.fill(value)

            if result.success:
                return ActionExecutionResult(
                    success=True,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=f"Filled {step.field_name or step.selector}",
                    metadata={
                        "selector": step.selector,
                        "field_name": step.field_name,
                        "value_length": len(value),
                    },
                )
            else:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=result.message,
                    metadata={"selector": step.selector},
                )

        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message=f"Fill failed: {str(e)}",
            )

    async def execute_click(
        self,
        step: ExecutionPlanStep,
        session: ApplicationSession,
    ) -> ActionExecutionResult:
        """
        Execute SUBMIT_APPLICATION or CONTINUE_TO_NEXT_STEP (click actions).

        Args:
            step: ExecutionPlanStep with click action
            session: ApplicationSession context

        Returns:
            ActionExecutionResult
        """
        if not step.selector:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message="No selector provided for click action",
            )

        try:
            # Find element
            element = await self.adapter.find_element(step.selector)
            if not element:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=f"Element not found: {step.selector}",
                    metadata={"selector": step.selector},
                )

            # Click element (await async operation)
            result = await element.click()

            if result.success:
                return ActionExecutionResult(
                    success=True,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=f"Clicked {step.field_name or step.selector}",
                    metadata={
                        "selector": step.selector,
                        "field_name": step.field_name,
                    },
                )
            else:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=result.message,
                    metadata={"selector": step.selector},
                )

        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message=f"Click failed: {str(e)}",
            )

    async def execute_upload(
        self,
        step: ExecutionPlanStep,
        session: ApplicationSession,
    ) -> ActionExecutionResult:
        """
        Execute UPLOAD_RESUME or UPLOAD_DOCUMENTS action.

        Args:
            step: ExecutionPlanStep with upload action
            session: ApplicationSession context

        Returns:
            ActionExecutionResult
        """
        if not step.selector:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message="No selector provided for upload action",
            )

        try:
            # Get file path
            file_path = step.expected_value or ""
            if step.value_source == "profile.resume_path":
                file_path = await self._resolve_value_from_metadata(step, session)
            elif step.value_source == "file_path":
                file_path = step.expected_value or ""

            if not file_path:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message="No file path provided for upload",
                )

            # Find element
            element = await self.adapter.find_element(step.selector)
            if not element:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=f"Upload element not found: {step.selector}",
                    metadata={"selector": step.selector},
                )

            # Upload file (await async operation - use upload_file not fill)
            result = await element.upload_file(file_path)

            if result.success:
                return ActionExecutionResult(
                    success=True,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=f"Uploaded {step.field_name or 'file'}",
                    metadata={
                        "selector": step.selector,
                        "field_name": step.field_name,
                        "file_path": file_path,
                    },
                )
            else:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=result.message,
                    metadata={"selector": step.selector},
                )

        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message=f"Upload failed: {str(e)}",
            )

    async def execute_confirm(
        self,
        step: ExecutionPlanStep,
        session: ApplicationSession,
    ) -> ActionExecutionResult:
        """
        Execute CONFIRM_APPLICATION action (user review).

        Args:
            step: ExecutionPlanStep with confirm action
            session: ApplicationSession context

        Returns:
            ActionExecutionResult
        """
        # Confirmation is typically manual review - just record it
        return ActionExecutionResult(
            success=True,
            action=str(step.action),
            step_number=step.step_number,
            message="Application ready for review",
            metadata={
                "requires_user_action": True,
                "field_name": step.field_name or "review",
            },
        )

    async def execute_validation(
        self,
        step: ExecutionPlanStep,
        session: ApplicationSession,
    ) -> ActionExecutionResult:
        """
        Execute VERIFY_SUBMISSION action.

        Args:
            step: ExecutionPlanStep with validation action
            session: ApplicationSession context

        Returns:
            ActionExecutionResult
        """
        try:
            # Get page to check for confirmation
            page = await self.adapter.get_page()

            # Look for confirmation patterns in page
            confirmation_patterns = step.metadata.get(
                "selector_patterns", ["confirmation", "success", "submitted"]
            )
            page_content = page.extract_html().lower()

            found_patterns = [p for p in confirmation_patterns if p in page_content]

            if found_patterns:
                return ActionExecutionResult(
                    success=True,
                    action=str(step.action),
                    step_number=step.step_number,
                    message="Submission verified successfully",
                    metadata={
                        "found_patterns": found_patterns,
                        "page_title": page.title,
                    },
                )
            else:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message="Could not verify submission",
                    metadata={
                        "looked_for_patterns": confirmation_patterns,
                        "page_title": page.title,
                    },
                )

        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message=f"Validation failed: {str(e)}",
            )

    async def execute_select(
        self,
        step: ExecutionPlanStep,
        session: ApplicationSession,
    ) -> ActionExecutionResult:
        """
        Execute SELECT_OPTIONS action.

        Args:
            step: ExecutionPlanStep with select action
            session: ApplicationSession context

        Returns:
            ActionExecutionResult
        """
        if not step.selector:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message="No selector provided for select action",
            )

        try:
            # Find element
            element = await self.adapter.find_element(step.selector)
            if not element:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=f"Select element not found: {step.selector}",
                    metadata={"selector": step.selector},
                )

            # Get value to select
            value = step.expected_value or ""

            # Use select_option() for <select> elements (not fill)
            result = await element.select_option(value)

            if result.success:
                return ActionExecutionResult(
                    success=True,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=f"Selected option: {value}",
                    metadata={
                        "selector": step.selector,
                        "option": value,
                    },
                )
            else:
                return ActionExecutionResult(
                    success=False,
                    action=str(step.action),
                    step_number=step.step_number,
                    message=result.message,
                    metadata={"selector": step.selector},
                )

        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action=str(step.action),
                step_number=step.step_number,
                message=f"Select failed: {str(e)}",
            )

    async def _resolve_value_from_profile(
        self, field_name: str, session: ApplicationSession
    ) -> str:
        """Resolve value from user profile."""
        # Placeholder: in real implementation, would fetch from session.user_profile
        return f"[Profile value for {field_name}]"

    async def _resolve_value_from_metadata(
        self, step: ExecutionPlanStep, session: ApplicationSession
    ) -> str:
        """Resolve value from step metadata or session."""
        if step.expected_value:
            return step.expected_value

        # Check metadata for value hints
        metadata_value = step.metadata.get("value")
        if metadata_value:
            return metadata_value

        # Fallback to placeholder
        return f"[Value for {step.field_name}]"

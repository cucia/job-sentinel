"""
Execution Engine

Consumes ExecutionPlan objects and produces ExecutionResult objects.
Supports both simulation (Phase 5) and real execution via ActionExecutor (Phase 8+).

Phase 5: Simulation-only execution
Phase 8: ActionExecutor integration for real browser automation
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from backend.application.session import ApplicationSession
from backend.application.execution_planner import ExecutionPlan
from backend.execution.result import ExecutionResult
from backend.execution.state_tracker import StateTracker
from src.core.logger import log

if TYPE_CHECKING:
    from backend.execution.action_executor import ActionExecutor


class ExecutionEngine:
    """Executes ApplicationSession plans and produces results."""

    def __init__(self, action_executor: Optional["ActionExecutor"] = None):
        """
        Initialize execution engine.

        Args:
            action_executor: Optional ActionExecutor for real execution.
                           If None, uses simulation mode.
        """
        self.action_executor = action_executor

    async def execute(
        self,
        session: ApplicationSession,
        plan: ExecutionPlan,
        dry_run: bool = True,
    ) -> ExecutionResult:
        """
        Execute a plan and return result.

        Args:
            session: ApplicationSession with execution context
            plan: ExecutionPlan to execute
            dry_run: If True, simulate execution without browser/forms

        Returns:
            ExecutionResult with outcome
        """
        log(f"[ExecutionEngine] Starting execution")
        log(f"  - Session: {session.session_id}")
        log(f"  - Plan: {plan.plan_id}")
        log(f"  - Steps: {len(plan.steps)}")
        log(f"  - Dry run: {dry_run}")

        start_time = datetime.utcnow()

        # Validate plan structure
        if not self._validate_plan(plan):
            return ExecutionResult(
                success=False,
                status="failed",
                completed_steps=0,
                errors=["Invalid plan structure"],
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                execution_plan_id=plan.plan_id,
                started_at=start_time,
                completed_at=datetime.utcnow(),
            )

        # Initialize state tracker
        tracker = StateTracker(plan.plan_id, len(plan.steps))
        tracker.start_execution()

        # Execute each step
        for step in plan.steps:
            log(f"[ExecutionEngine] Step {step.step_number}: {step.action}")

            # Route to ActionExecutor if available and not dry_run
            if self.action_executor and not dry_run:
                try:
                    action_result = await self.action_executor.execute_step(step, session)
                    success = action_result.success

                    if success:
                        tracker.complete_step(
                            step.step_number,
                            step.description,
                            step.estimated_duration_seconds,
                            action_result.metadata,
                        )
                    else:
                        tracker.fail_step(
                            step.step_number,
                            step.description,
                            action_result.message,
                            action_result.metadata,
                        )
                except Exception as e:
                    log(f"[ExecutionEngine] Exception executing step {step.step_number}: {e}")
                    tracker.fail_step(
                        step.step_number,
                        step.description,
                        f"Exception: {str(e)}",
                    )
                    success = False
            else:
                # Use simulation mode (Phase 5 fallback or explicit dry_run)
                success = self._simulate_step_execution(session, step, tracker, dry_run)

            if not success:
                log(f"[ExecutionEngine] Step {step.step_number} failed")
                break

        # Finish execution
        success = len(tracker.failed_steps) == 0
        tracker.finish_execution(success)

        # Update session with execution history
        session.execution_history.append(tracker.get_state())

        # Create result
        result = ExecutionResult(
            success=success,
            status=tracker.status,
            completed_steps=len(tracker.completed_steps),
            failed_step=tracker.failed_steps[0] if tracker.failed_steps else None,
            errors=[h.get("error", "") for h in tracker.step_history if h.get("status") == "failed"],
            execution_time=tracker.get_execution_time(),
            metadata=tracker.get_state(),
            execution_plan_id=plan.plan_id,
            started_at=start_time,
            completed_at=datetime.utcnow(),
        )

        log(f"[ExecutionEngine] Execution finished")
        log(f"  - Success: {result.success}")
        log(f"  - Completed steps: {result.completed_steps}/{len(plan.steps)}")
        log(f"  - Execution time: {result.execution_time:.2f}s")

        return result

    def _validate_plan(self, plan: ExecutionPlan) -> bool:
        """
        Validate plan structure.

        Args:
            plan: ExecutionPlan to validate

        Returns:
            True if valid, False otherwise
        """
        # Check plan has ID
        if not plan.plan_id:
            log(f"[ExecutionEngine] Invalid: missing plan_id")
            return False

        # Check plan has steps
        if len(plan.steps) == 0:
            # Empty plans are valid (nothing to execute)
            log(f"[ExecutionEngine] Warning: empty plan (0 steps)")
            return True

        # Check step ordering
        for i, step in enumerate(plan.steps):
            if step.step_number != i + 1:
                log(f"[ExecutionEngine] Invalid: step numbering incorrect")
                return False

            if not step.action:
                log(f"[ExecutionEngine] Invalid: step {i+1} missing action")
                return False

        return True

    def _simulate_step_execution(
        self,
        session: ApplicationSession,
        step,
        tracker: StateTracker,
        dry_run: bool = True,
    ) -> bool:
        """
        Simulate execution of a single step.

        In foundation phase, this validates step metadata.
        Future: Will integrate with browser_worker.py and Playwright.

        Args:
            session: ApplicationSession
            step: ExecutionPlanStep to execute
            tracker: StateTracker to update
            dry_run: If True, simulate without actually executing

        Returns:
            True if step succeeded, False otherwise
        """
        # Validate step has required fields
        if not step.action or not step.description:
            tracker.fail_step(
                step.step_number,
                step.description or "unknown",
                "Invalid step: missing action or description",
            )
            return False

        # Simulate step execution
        if dry_run:
            # In dry run, all steps succeed (validation only)
            tracker.complete_step(
                step.step_number,
                step.description,
                step.estimated_duration_seconds,
                {"simulated": True, "action": str(step.action)},
            )
            return True

        # Future: Replace with actual browser automation
        # This is where browser_worker.py integration will happen
        # For now, simulate success
        tracker.complete_step(
            step.step_number,
            step.description,
            step.estimated_duration_seconds,
            {"action": str(step.action), "validation_checks": step.validation_checks},
        )
        return True

    def record_execution_in_session(self, session: ApplicationSession, result: ExecutionResult):
        """
        Record execution result in session.

        Args:
            session: ApplicationSession to update
            result: ExecutionResult to record
        """
        session.execution_history.append(result.to_dict())
        session.last_execution_result = result

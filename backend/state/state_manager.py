from typing import Optional, Callable, List
from datetime import datetime
from backend.runtime.task_model import Task, TaskStatus, TaskResult


class StateManager:
    """Centralized task state management with explicit transitions."""

    def __init__(self, storage, event_bus=None):
        """
        Initialize state manager.

        Args:
            storage: Storage layer for persistence
            event_bus: Optional event bus for state change notifications
        """
        self.storage = storage
        self.event_bus = event_bus
        self._transition_validators: dict[tuple[TaskStatus, TaskStatus], Callable] = {}
        self._setup_validators()

    def _setup_validators(self) -> None:
        """Define valid state transitions."""
        # DISCOVERED -> QUEUED
        self._transition_validators[(TaskStatus.DISCOVERED, TaskStatus.QUEUED)] = lambda t: True

        # QUEUED -> RUNNING
        self._transition_validators[(TaskStatus.QUEUED, TaskStatus.RUNNING)] = lambda t: t.worker_id is not None

        # RUNNING -> COMPLETED
        self._transition_validators[(TaskStatus.RUNNING, TaskStatus.COMPLETED)] = lambda t: t.result is not None

        # RUNNING -> FAILED
        self._transition_validators[(TaskStatus.RUNNING, TaskStatus.FAILED)] = lambda t: t.error_message is not None

        # RUNNING -> MANUAL_REVIEW
        self._transition_validators[(TaskStatus.RUNNING, TaskStatus.MANUAL_REVIEW)] = (
            lambda t: t.manual_review_context is not None
        )

        # FAILED -> QUEUED (retry)
        self._transition_validators[(TaskStatus.FAILED, TaskStatus.QUEUED)] = lambda t: t.is_retryable()

    def _is_valid_transition(self, from_status: TaskStatus, to_status: TaskStatus, task: Task) -> bool:
        """Check if state transition is valid."""
        key = (from_status, to_status)
        if key not in self._transition_validators:
            return False
        validator = self._transition_validators[key]
        return validator(task)

    def _emit_event(self, event_type: str, task: Task) -> None:
        """Emit state change event if event bus available."""
        if self.event_bus:
            self.event_bus.emit(event_type, {"task": task.to_dict()})

    def create_task(self, task_id: str, job_id: str, source_platform: str, priority: int = 0) -> Task:
        """
        Create new task in DISCOVERED state.

        Args:
            task_id: Unique task identifier
            job_id: Job identifier
            source_platform: Platform name (linkedin, indeed, naukri)
            priority: Task priority (higher = earlier execution)

        Returns:
            Created task
        """
        task = Task(
            task_id=task_id,
            job_id=job_id,
            source_platform=source_platform,
            status=TaskStatus.DISCOVERED,
            priority=priority,
        )
        self.storage.save_task(task)
        self._emit_event("TASK_CREATED", task)
        return task

    def transition_to_queued(self, task: Task) -> None:
        """
        Transition task from DISCOVERED to QUEUED.

        Args:
            task: Task to transition
        """
        if not self._is_valid_transition(task.status, TaskStatus.QUEUED, task):
            raise ValueError(f"Cannot transition from {task.status} to QUEUED")
        task.status = TaskStatus.QUEUED
        task.updated_at = datetime.utcnow()
        self.storage.save_task(task)
        self._emit_event("TASK_QUEUED", task)

    def transition_to_running(self, task: Task, worker_id: str) -> None:
        """
        Transition task from QUEUED to RUNNING.

        Args:
            task: Task to transition
            worker_id: Worker executing the task
        """
        task.worker_id = worker_id
        if not self._is_valid_transition(task.status, TaskStatus.RUNNING, task):
            raise ValueError(f"Cannot transition from {task.status} to RUNNING")
        task.mark_running(worker_id)
        self.storage.save_task(task)
        self._emit_event("TASK_STARTED", task)

    def transition_to_completed(self, task: Task, result: TaskResult) -> None:
        """
        Transition task from RUNNING to COMPLETED.

        Args:
            task: Task to transition
            result: Task execution result
        """
        task.result = result
        if not self._is_valid_transition(task.status, TaskStatus.COMPLETED, task):
            raise ValueError(f"Cannot transition from {task.status} to COMPLETED")
        task.mark_completed(result)
        self.storage.save_task(task)
        self._emit_event("TASK_COMPLETED", task)

    def transition_to_failed(self, task: Task, error: str) -> None:
        """
        Transition task from RUNNING to FAILED.

        Args:
            task: Task to transition
            error: Error message
        """
        task.error_message = error
        if not self._is_valid_transition(task.status, TaskStatus.FAILED, task):
            raise ValueError(f"Cannot transition from {task.status} to FAILED")
        task.mark_failed(error)
        self.storage.save_task(task)
        self._emit_event("TASK_FAILED", task)

    def transition_to_manual_review(self, task: Task, context: dict) -> None:
        """
        Transition task from RUNNING to MANUAL_REVIEW.

        Args:
            task: Task to transition
            context: Review context (state, error, etc.)
        """
        task.manual_review_context = context
        if not self._is_valid_transition(task.status, TaskStatus.MANUAL_REVIEW, task):
            raise ValueError(f"Cannot transition from {task.status} to MANUAL_REVIEW")
        task.mark_manual_review(context)
        self.storage.save_task(task)

    def retry_task(self, task: Task) -> None:
        """
        Transition task from FAILED back to QUEUED for retry.

        Args:
            task: Task to retry
        """
        if not self._is_valid_transition(task.status, TaskStatus.QUEUED, task):
            raise ValueError(f"Cannot retry task in {task.status} state")
        task.retry()
        self.storage.save_task(task)
        self._emit_event("TASK_RETRIED", task)

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Retrieve task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task or None if not found
        """
        return self.storage.get_task(task_id)

    def get_tasks_by_status(self, status: TaskStatus, limit: int = 100) -> List[Task]:
        """
        Retrieve tasks by status.

        Args:
            status: Task status to filter by
            limit: Maximum number of tasks

        Returns:
            List of tasks with given status
        """
        return self.storage.get_tasks_by_status(status, limit=limit)

    def get_task_history(self, task_id: str) -> List[dict]:
        """
        Retrieve state transition history for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of state transitions with timestamps
        """
        return self.storage.get_task_history(task_id)

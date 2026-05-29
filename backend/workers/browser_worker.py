from abc import ABC, abstractmethod
from typing import Optional
from backend.runtime.task_model import Task, TaskResult


class Worker(ABC):
    """Base worker class for task execution."""

    def __init__(self, worker_id: str):
        """
        Initialize worker.

        Args:
            worker_id: Unique worker identifier
        """
        self.worker_id = worker_id

    @abstractmethod
    async def execute(self, task: Task) -> TaskResult:
        """
        Execute task.

        Args:
            task: Task to execute

        Returns:
            TaskResult indicating outcome
        """
        pass

    @abstractmethod
    def can_handle(self, task: Task) -> bool:
        """
        Check if worker can handle task.

        Args:
            task: Task to check

        Returns:
            True if worker can execute task
        """
        pass


class BrowserWorker(Worker):
    """Worker that executes job applications via browser automation."""

    def __init__(self, worker_id: str, apply_functions: dict, settings: dict, profile: dict, resume_path: str):
        """
        Initialize browser worker.

        Args:
            worker_id: Unique worker identifier
            apply_functions: Dict mapping platform -> apply function
            settings: Application settings
            profile: User profile
            resume_path: Path to resume file
        """
        super().__init__(worker_id)
        self.apply_functions = apply_functions
        self.settings = settings
        self.profile = profile
        self.resume_path = resume_path

    def can_handle(self, task: Task) -> bool:
        """Check if platform has apply function."""
        return task.source_platform in self.apply_functions

    async def execute(self, task: Task) -> TaskResult:
        """
        Execute job application.

        Args:
            task: Task containing job to apply for

        Returns:
            TaskResult (APPLIED, REVIEW, SKIPPED, or FAILED)
        """
        if not self.can_handle(task):
            return TaskResult.SKIPPED

        platform = task.source_platform
        apply_fn = self.apply_functions[platform]
        job = task.metadata.get("job", {})

        try:
            # Call apply function (may be sync or async)
            result = apply_fn(job, self.resume_path, self.settings)

            # Handle tuple result (status, easy_apply)
            if isinstance(result, tuple):
                status, easy_apply = result
                task.metadata["easy_apply"] = easy_apply
            else:
                status = result

            # Map status to TaskResult
            if status == "applied":
                return TaskResult.APPLIED
            elif status == "review":
                return TaskResult.REVIEW
            elif status == "skipped":
                return TaskResult.SKIPPED
            else:
                return TaskResult.DEFERRED

        except Exception as e:
            task.metadata["error"] = str(e)
            raise


class RecoveryWorker(Worker):
    """Worker that handles task recovery and retry logic."""

    def __init__(self, worker_id: str, state_manager, queue):
        """
        Initialize recovery worker.

        Args:
            worker_id: Unique worker identifier
            state_manager: State manager for task transitions
            queue: Queue system for retry operations
        """
        super().__init__(worker_id)
        self.state_manager = state_manager
        self.queue = queue

    def can_handle(self, task: Task) -> bool:
        """Recovery worker handles failed tasks."""
        return task.is_retryable()

    async def execute(self, task: Task) -> TaskResult:
        """
        Attempt task recovery.

        Args:
            task: Failed task to recover

        Returns:
            TaskResult.QUEUED if retry queued, else FAILED
        """
        if not task.is_retryable():
            return TaskResult.FAILED

        try:
            self.queue.retry(task)
            return TaskResult.QUEUED
        except Exception as e:
            task.metadata["recovery_error"] = str(e)
            raise


class WorkerPool:
    """Pool of workers for task execution."""

    def __init__(self):
        """Initialize worker pool."""
        self._workers: dict[str, Worker] = {}

    def register(self, worker: Worker) -> None:
        """
        Register worker.

        Args:
            worker: Worker to register
        """
        self._workers[worker.worker_id] = worker

    def unregister(self, worker_id: str) -> None:
        """
        Unregister worker.

        Args:
            worker_id: Worker identifier
        """
        if worker_id in self._workers:
            del self._workers[worker_id]

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """
        Retrieve worker by ID.

        Args:
            worker_id: Worker identifier

        Returns:
            Worker or None if not found
        """
        return self._workers.get(worker_id)

    def find_worker_for_task(self, task: Task) -> Optional[Worker]:
        """
        Find suitable worker for task.

        Args:
            task: Task to execute

        Returns:
            Worker that can handle task, or None
        """
        for worker in self._workers.values():
            if worker.can_handle(task):
                return worker
        return None

    def get_all_workers(self) -> list[Worker]:
        """
        Get all registered workers.

        Returns:
            List of workers
        """
        return list(self._workers.values())

    def get_worker_count(self) -> int:
        """
        Get number of registered workers.

        Returns:
            Worker count
        """
        return len(self._workers)

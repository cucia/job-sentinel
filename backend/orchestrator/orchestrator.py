import asyncio
from typing import Optional, List
from datetime import datetime
from backend.runtime.task_model import Task, TaskStatus, TaskResult
from backend.queue.queue import Queue
from backend.state.state_manager import StateManager
from backend.workers.browser_worker import WorkerPool
from backend.manual_review.review_queue import ManualReviewQueue


class RuntimeOrchestrator:
    """Central execution authority for task orchestration."""

    def __init__(
        self,
        queue: Queue,
        state_manager: StateManager,
        worker_pool: WorkerPool,
        manual_review_queue: ManualReviewQueue,
        max_concurrent_tasks: int = 5,
    ):
        """
        Initialize orchestrator.

        Args:
            queue: Task queue system
            state_manager: State management system
            worker_pool: Pool of available workers
            manual_review_queue: Manual review queue
            max_concurrent_tasks: Maximum concurrent task executions
        """
        self.queue = queue
        self.state_manager = state_manager
        self.worker_pool = worker_pool
        self.manual_review_queue = manual_review_queue
        self.max_concurrent_tasks = max_concurrent_tasks
        self._active_tasks: dict[str, Task] = {}
        self._running = False

    async def start(self) -> None:
        """Start orchestrator event loop."""
        self._running = True
        try:
            while self._running:
                await self._process_batch()
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Orchestrator error: {e}")
            self._running = False

    def stop(self) -> None:
        """Stop orchestrator."""
        self._running = False

    async def _process_batch(self) -> None:
        """Process batch of queued tasks."""
        # Check for available worker slots
        available_slots = self.max_concurrent_tasks - len(self._active_tasks)
        if available_slots <= 0:
            return

        # Dequeue tasks
        tasks = self.queue.dequeue(limit=available_slots)
        if not tasks:
            return

        # Execute tasks concurrently
        execution_tasks = [self._execute_task(task) for task in tasks]
        await asyncio.gather(*execution_tasks, return_exceptions=True)

    async def _execute_task(self, task: Task) -> None:
        """
        Execute single task with full lifecycle management.

        Args:
            task: Task to execute
        """
        self._active_tasks[task.task_id] = task

        try:
            # Find suitable worker
            worker = self.worker_pool.find_worker_for_task(task)
            if not worker:
                await self._handle_no_worker(task)
                return

            # Transition to running
            self.state_manager.transition_to_running(task, worker.worker_id)

            # Execute task
            result = await worker.execute(task)

            # Handle result
            await self._handle_result(task, result)

        except Exception as e:
            await self._handle_execution_error(task, str(e))

        finally:
            self._active_tasks.pop(task.task_id, None)

    async def _handle_result(self, task: Task, result: TaskResult) -> None:
        """
        Handle task execution result.

        Args:
            task: Executed task
            result: Execution result
        """
        if result == TaskResult.APPLIED:
            self.state_manager.transition_to_completed(task, result)
        elif result == TaskResult.REVIEW:
            context = {
                "reason": "manual_review_required",
                "metadata": task.metadata,
            }
            self.state_manager.transition_to_manual_review(task, context)
            self.manual_review_queue.enqueue(task, context)
        elif result == TaskResult.SKIPPED:
            self.state_manager.transition_to_completed(task, result)
        elif result == TaskResult.DEFERRED:
            self.state_manager.transition_to_completed(task, result)
        elif result == TaskResult.FAILED:
            await self._handle_execution_error(task, "Worker returned FAILED")

    async def _handle_execution_error(self, task: Task, error: str) -> None:
        """
        Handle task execution error.

        Args:
            task: Failed task
            error: Error message
        """
        if task.is_retryable():
            # Retry
            self.state_manager.transition_to_failed(task, error)
            self.queue.retry(task)
        else:
            # Escalate to manual review
            context = {
                "reason": "execution_error",
                "error": error,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "metadata": task.metadata,
            }
            self.state_manager.transition_to_manual_review(task, context)
            self.manual_review_queue.enqueue(task, context)

    async def _handle_no_worker(self, task: Task) -> None:
        """
        Handle case where no suitable worker found.

        Args:
            task: Task with no available worker
        """
        context = {
            "reason": "no_worker_available",
            "platform": task.source_platform,
            "metadata": task.metadata,
        }
        self.state_manager.transition_to_manual_review(task, context)
        self.manual_review_queue.enqueue(task, context)

    def get_active_task_count(self) -> int:
        """
        Get number of currently executing tasks.

        Returns:
            Count of active tasks
        """
        return len(self._active_tasks)

    def get_queue_size(self) -> int:
        """
        Get number of queued tasks.

        Returns:
            Count of queued tasks
        """
        return self.queue.get_queue_size()

    def get_status(self) -> dict:
        """
        Get orchestrator status.

        Returns:
            Status dict with queue size, active tasks, etc.
        """
        return {
            "running": self._running,
            "active_tasks": self.get_active_task_count(),
            "queue_size": self.get_queue_size(),
            "max_concurrent": self.max_concurrent_tasks,
            "workers": self.worker_pool.get_worker_count(),
        }

    async def process_single_task(self, task_id: str) -> Optional[Task]:
        """
        Process single task by ID (for testing/manual execution).

        Args:
            task_id: Task identifier

        Returns:
            Processed task or None if not found
        """
        task = self.state_manager.get_task(task_id)
        if not task:
            return None

        if task.status != TaskStatus.QUEUED:
            raise ValueError(f"Task must be in QUEUED state, currently {task.status}")

        await self._execute_task(task)
        return task

    def enqueue_task(
        self,
        task_id: str,
        job_id: str,
        source_platform: str,
        priority: int = 0,
        metadata: dict = None,
    ) -> Task:
        """
        Create and enqueue new task.

        Args:
            task_id: Unique task identifier
            job_id: Job identifier
            source_platform: Platform name
            priority: Task priority
            metadata: Additional task metadata

        Returns:
            Created task
        """
        task = self.state_manager.create_task(task_id, job_id, source_platform, priority)
        if metadata:
            task.metadata.update(metadata)
        self.state_manager.transition_to_queued(task)
        return task

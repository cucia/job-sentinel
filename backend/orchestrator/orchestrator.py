import asyncio
from typing import Optional, List
from datetime import datetime
from backend.runtime.task_model import Task, TaskStatus, TaskResult
from backend.queue.queue import Queue
from backend.state.state_manager import StateManager
from backend.workers.browser_worker import WorkerPool
from backend.manual_review.review_queue import ManualReviewQueue
from backend.workflow.handlers import WorkflowHandlerRegistry
from src.core.logger import log


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
        # Initialize workflow routing
        self.workflow_registry = WorkflowHandlerRegistry()

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
        Execute single task with workflow-aware routing.

        Args:
            task: Task to execute
        """
        self._active_tasks[task.task_id] = task

        try:
            # Route to workflow handler
            workflow_result = self._route_to_workflow(task)

            if not workflow_result.get("valid", False):
                log(f"[Orchestrator] Task {task.task_id} workflow routing failed: {workflow_result.get('reason')}")
                await self._handle_execution_error(task, workflow_result.get("reason", "Unknown error"))
                return

            log(f"[Orchestrator] Task {task.task_id} routed to {workflow_result.get('handler')}")
            log(f"  - Next step: {workflow_result.get('next_step')}")
            log(f"  - Requires: {workflow_result.get('requires')}")

            # Transition to running
            self.state_manager.transition_to_running(task, "workflow_handler")

            # In Phase 3+, execute task based on workflow_result
            # For now, just mark as completed for routing validation
            result = TaskResult.APPLIED
            await self._handle_result(task, result)

        except Exception as e:
            await self._handle_execution_error(task, str(e))

        finally:
            self._active_tasks.pop(task.task_id, None)

    def _route_to_workflow(self, task: Task) -> dict:
        """
        Route task to appropriate workflow handler.

        Args:
            task: Task to route

        Returns:
            Routing result dict with handler info and preparation data
        """
        if not task.workflow_type:
            return {
                "valid": False,
                "reason": "No workflow_type attached to task",
            }

        routing_result = self.workflow_registry.route_task(task)

        log(f"[Orchestrator] Routing task {task.task_id}")
        log(f"  - Workflow type: {task.workflow_type}")
        log(f"  - Execution strategy: {task.execution_strategy}")
        log(f"  - Confidence: {task.workflow_confidence:.0%}")

        return routing_result

    def _log_workflow_classification(self, task: Task) -> None:
        """
        Log workflow classification information for task.

        Args:
            task: Task to log classification for
        """
        if task.workflow_type:
            print(f"[Orchestrator] Task {task.task_id}:")
            print(f"  - Workflow Type: {task.workflow_type}")
            print(f"  - Execution Strategy: {task.execution_strategy}")
            print(f"  - Confidence: {task.workflow_confidence:.0%}")
            print(f"  - Indicators: {len(task.workflow_indicators)} detected")

    def get_task_workflow_info(self, task_id: str) -> dict:
        """
        Get workflow classification info for a task.

        Args:
            task_id: Task identifier

        Returns:
            Dict with workflow type, strategy, and confidence
        """
        task = self._active_tasks.get(task_id)
        if not task:
            return {}

        return {
            "workflow_type": task.workflow_type,
            "execution_strategy": task.execution_strategy,
            "workflow_confidence": task.workflow_confidence,
            "workflow_indicators": task.workflow_indicators,
        }

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

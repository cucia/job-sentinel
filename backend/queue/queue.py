from typing import Optional, List
from datetime import datetime
from backend.runtime.task_model import Task, TaskStatus


class Queue:
    """Task queue system with priority and retry support."""

    def __init__(self, storage):
        """
        Initialize queue with storage backend.

        Args:
            storage: Storage layer (e.g., SQLite wrapper)
        """
        self.storage = storage

    def enqueue(self, task: Task) -> None:
        """
        Add task to queue.

        Args:
            task: Task to enqueue
        """
        if task.status != TaskStatus.DISCOVERED:
            raise ValueError(f"Cannot enqueue task in {task.status} state")
        task.status = TaskStatus.QUEUED
        task.updated_at = datetime.utcnow()
        self.storage.save_task(task)

    def dequeue(self, limit: int = 1) -> List[Task]:
        """
        Retrieve tasks from queue, ordered by priority and creation time.

        Args:
            limit: Maximum number of tasks to retrieve

        Returns:
            List of tasks ready to execute
        """
        return self.storage.get_queued_tasks(limit=limit, order_by="priority DESC, created_at ASC")

    def peek(self) -> Optional[Task]:
        """
        Peek at next task without removing from queue.

        Returns:
            Next task or None if queue empty
        """
        tasks = self.dequeue(limit=1)
        return tasks[0] if tasks else None

    def retry(self, task: Task) -> None:
        """
        Prepare task for retry.

        Args:
            task: Task to retry
        """
        if not task.is_retryable():
            raise ValueError(f"Task cannot be retried (retries: {task.retry_count}/{task.max_retries})")
        task.retry()
        self.storage.save_task(task)

    def move_to_manual_review(self, task: Task, context: dict) -> None:
        """
        Escalate task to manual review queue.

        Args:
            task: Task to escalate
            context: Review context (state, error, etc.)
        """
        task.mark_manual_review(context)
        self.storage.save_task(task)
        self.storage.save_manual_review_record(task)

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

    def get_queue_size(self) -> int:
        """
        Get number of queued tasks.

        Returns:
            Count of tasks in QUEUED state
        """
        return self.storage.count_tasks_by_status(TaskStatus.QUEUED)

    def get_failed_tasks(self, limit: int = 100) -> List[Task]:
        """
        Retrieve failed tasks eligible for retry.

        Returns:
            List of failed tasks that can be retried
        """
        failed = self.storage.get_tasks_by_status(TaskStatus.FAILED, limit=limit)
        return [t for t in failed if t.is_retryable()]

    def get_manual_review_tasks(self, limit: int = 100) -> List[Task]:
        """
        Retrieve tasks awaiting manual review.

        Returns:
            List of tasks in MANUAL_REVIEW state
        """
        return self.storage.get_tasks_by_status(TaskStatus.MANUAL_REVIEW, limit=limit)

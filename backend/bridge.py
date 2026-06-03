"""
Bridge module to integrate Phase 1 runtime with existing controller.

This module provides adapters to use the new runtime infrastructure
while maintaining backward compatibility with existing code.
"""

import os
from datetime import datetime
from backend.runtime.task_model import Task, TaskStatus, TaskResult
from backend.persistence.task_storage import TaskStorage
from backend.queue.queue import Queue
from backend.state.state_manager import StateManager
from backend.events.event_bus import EventBus
from backend.workers.browser_worker import WorkerPool, BrowserWorker
from backend.manual_review.review_queue import ManualReviewQueue
from backend.orchestrator.orchestrator import RuntimeOrchestrator
from backend.workflow_classification import create_classifier
from src.core.logger import log


class RuntimeBridge:
    """Bridge between existing controller and new runtime infrastructure."""

    def __init__(self, db_path: str, settings: dict, profile: dict, platforms: dict, resume_path: str):
        """
        Initialize runtime bridge.

        Args:
            db_path: Path to SQLite database
            settings: Application settings
            profile: User profile
            platforms: Dict mapping platform -> apply function
            resume_path: Path to resume file
        """
        self.db_path = db_path
        self.settings = settings
        self.profile = profile
        self.platforms = platforms
        self.resume_path = resume_path

        # Initialize workflow classifier
        self.classifier = create_classifier()

        # Initialize runtime infrastructure
        self.storage = TaskStorage(db_path)
        self.event_bus = EventBus()
        self.queue = Queue(self.storage)
        self.state_manager = StateManager(self.storage, self.event_bus)
        self.manual_review_queue = ManualReviewQueue(self.storage)

        # Initialize worker pool
        self.worker_pool = WorkerPool()
        browser_worker = BrowserWorker(
            worker_id="browser-worker-1",
            apply_functions=platforms,
            settings=settings,
            profile=profile,
            resume_path=resume_path,
        )
        self.worker_pool.register(browser_worker)

        # Initialize orchestrator
        self.orchestrator = RuntimeOrchestrator(
            queue=self.queue,
            state_manager=self.state_manager,
            worker_pool=self.worker_pool,
            manual_review_queue=self.manual_review_queue,
            max_concurrent_tasks=int(settings.get("app", {}).get("max_concurrent_tasks", 5)),
        )

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup event logging."""
        def log_event(event_type):
            def handler(data):
                task = data.get("task", {})
                log(f"[Runtime] {event_type}: task={task.get('task_id')} status={task.get('status')}")
            return handler

        self.event_bus.subscribe("TASK_CREATED", log_event("TASK_CREATED"))
        self.event_bus.subscribe("TASK_QUEUED", log_event("TASK_QUEUED"))
        self.event_bus.subscribe("TASK_STARTED", log_event("TASK_STARTED"))
        self.event_bus.subscribe("TASK_COMPLETED", log_event("TASK_COMPLETED"))
        self.event_bus.subscribe("TASK_FAILED", log_event("TASK_FAILED"))
        self.event_bus.subscribe("MANUAL_REVIEW_REQUIRED", log_event("MANUAL_REVIEW_REQUIRED"))

    def enqueue_job(self, job: dict, priority: int = 0) -> str:
        """
        Enqueue job for processing.

        Args:
            job: Job dict from collector
            priority: Task priority (higher = earlier execution)

        Returns:
            Task ID
        """
        from src.core.controller import _make_job_key

        job_key = _make_job_key(job)

        # Classify workflow
        job_url = job.get("url", "")
        job_title = job.get("title", "")
        classification = self.classifier.classify(url=job_url, page_title=job_title)

        # Create task with classification data
        task = self.orchestrator.enqueue_task(
            task_id=job_key,
            job_id=job_key,
            source_platform=job.get("platform", "unknown"),
            priority=priority,
            metadata={
                "job": job,
                "workflow_type": classification.workflow_type.value,
                "workflow_confidence": classification.confidence_score,
                "execution_strategy": classification.execution_strategy.value,
                "workflow_indicators": classification.indicators,
            },
        )

        log(f"[Bridge] Enqueued job: {job_key} platform={job.get('platform')} workflow={classification.workflow_type.value} confidence={classification.confidence_score:.0%}")
        return taskjob.get('platform')}")
        return task.task_id

    def enqueue_jobs(self, jobs: list, priority: int = 0) -> list:
        """
        Enqueue multiple jobs.

        Args:
            jobs: List of job dicts
            priority: Task priority

        Returns:
            List of task IDs
        """
        task_ids = []
        for job in jobs:
            try:
                task_id = self.enqueue_job(job, priority)
                task_ids.append(task_id)
            except Exception as e:
                log(f"[Bridge] Failed to enqueue job: {e}")
        return task_ids

    def get_queue_size(self) -> int:
        """Get number of queued tasks."""
        return self.queue.get_queue_size()

    def get_pending_reviews(self, limit: int = 100) -> list:
        """
        Get pending manual review records.

        Args:
            limit: Maximum number of records

        Returns:
            List of ManualReviewRecord dicts
        """
        records = self.manual_review_queue.get_pending(limit=limit)
        return [r.to_dict() for r in records]

    def get_review_stats(self) -> dict:
        """Get manual review queue statistics."""
        return self.manual_review_queue.get_review_stats()

    def get_task_status(self, task_id: str) -> dict:
        """
        Get task status.

        Args:
            task_id: Task identifier

        Returns:
            Task dict or None
        """
        task = self.state_manager.get_task(task_id)
        if task:
            return task.to_dict()
        return None

    def get_orchestrator_status(self) -> dict:
        """Get orchestrator status."""
        return self.orchestrator.get_status()

    def subscribe_to_events(self, event_type: str, handler) -> None:
        """
        Subscribe to runtime events.

        Args:
            event_type: Event type to subscribe to
            handler: Callable that receives event data
        """
        self.event_bus.subscribe(event_type, handler)

    def get_event_history(self, event_type: str = None, limit: int = 100) -> list:
        """
        Get event history.

        Args:
            event_type: Filter by event type (None = all)
            limit: Maximum number of events

        Returns:
            List of events
        """
        events = self.event_bus.get_history(event_type=event_type, limit=limit)
        return [e.to_dict() for e in events]


def create_runtime_bridge(base_dir: str, settings: dict, profile: dict, platforms: dict) -> RuntimeBridge:
    """
    Factory function to create runtime bridge.

    Args:
        base_dir: Base directory
        settings: Application settings
        profile: User profile
        platforms: Dict mapping platform -> apply function

    Returns:
        RuntimeBridge instance
    """
    from src.core.controller import _resolve_db_path

    db_path = _resolve_db_path(base_dir, settings)
    resume_path = settings.get("app", {}).get("resume_path", "resumes/resume.pdf")
    if not os.path.isabs(resume_path):
        resume_path = os.path.join(base_dir, resume_path)

    return RuntimeBridge(db_path, settings, profile, platforms, resume_path)

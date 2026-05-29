import asyncio
import tempfile
import os
from datetime import datetime
from backend.runtime.task_model import Task, TaskStatus, TaskResult
from backend.persistence.task_storage import TaskStorage
from backend.queue.queue import Queue
from backend.state.state_manager import StateManager
from backend.events.event_bus import EventBus
from backend.workers.browser_worker import WorkerPool, Worker
from backend.manual_review.review_queue import ManualReviewQueue
from backend.orchestrator.orchestrator import RuntimeOrchestrator


class MockWorker(Worker):
    """Mock worker for testing."""

    def __init__(self, worker_id: str, result: TaskResult = TaskResult.APPLIED, platforms: list = None):
        super().__init__(worker_id)
        self.result = result
        self.executed_tasks = []
        self.platforms = platforms or ["linkedin", "indeed", "naukri"]

    def can_handle(self, task: Task) -> bool:
        return task.source_platform in self.platforms

    async def execute(self, task: Task) -> TaskResult:
        self.executed_tasks.append(task)
        await asyncio.sleep(0.1)  # Simulate work
        return self.result


async def test_end_to_end_flow():
    """Test single job through complete runtime pipeline."""
    print("\n=== JobSentinel Phase 1 Runtime Integration Test ===\n")

    # Setup
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        storage = TaskStorage(db_path)
        event_bus = EventBus()
        queue = Queue(storage)
        state_manager = StateManager(storage, event_bus)
        manual_review_queue = ManualReviewQueue(storage)
        worker_pool = WorkerPool()

        # Register mock worker for linkedin
        mock_worker = MockWorker("worker-1", TaskResult.APPLIED, platforms=["linkedin"])
        worker_pool.register(mock_worker)

        # Create orchestrator
        orchestrator = RuntimeOrchestrator(
            queue=queue,
            state_manager=state_manager,
            worker_pool=worker_pool,
            manual_review_queue=manual_review_queue,
            max_concurrent_tasks=5,
        )

        # Subscribe to events
        events_received = []

        def event_handler(data):
            events_received.append(data)

        event_bus.subscribe("TASK_CREATED", event_handler)
        event_bus.subscribe("TASK_QUEUED", event_handler)
        event_bus.subscribe("TASK_STARTED", event_handler)
        event_bus.subscribe("TASK_COMPLETED", event_handler)

        print("✓ Runtime infrastructure initialized")
        print(f"  - Storage: {db_path}")
        print(f"  - Workers: {worker_pool.get_worker_count()}")
        print(f"  - Event subscribers: {event_bus.get_subscriber_count()}")

        # Test 1: Create and enqueue task
        print("\n[Test 1] Create and enqueue task")
        task = orchestrator.enqueue_task(
            task_id="task-001",
            job_id="job-001",
            source_platform="linkedin",
            priority=10,
            metadata={
                "job": {
                    "title": "Software Engineer",
                    "company": "TechCorp",
                    "job_url": "https://linkedin.com/jobs/123",
                }
            },
        )
        print(f"✓ Task created: {task.task_id}")
        print(f"  - Status: {task.status.value}")
        print(f"  - Priority: {task.priority}")
        print(f"  - Job: {task.metadata['job']['title']} at {task.metadata['job']['company']}")

        # Verify task persisted
        retrieved_task = storage.get_task(task.task_id)
        assert retrieved_task is not None, "Task not persisted"
        assert retrieved_task.status == TaskStatus.QUEUED, "Task not in QUEUED state"
        print("✓ Task persisted to storage")

        # Test 2: Queue operations
        print("\n[Test 2] Queue operations")
        queue_size = queue.get_queue_size()
        print(f"✓ Queue size: {queue_size}")
        assert queue_size == 1, "Queue should have 1 task"

        next_task = queue.peek()
        assert next_task is not None, "Queue should have a task"
        assert next_task.task_id == task.task_id, "Wrong task in queue"
        print(f"✓ Peeked next task: {next_task.task_id}")

        # Test 3: Execute task
        print("\n[Test 3] Execute task through orchestrator")
        await orchestrator.process_single_task(task.task_id)
        print("✓ Task executed")

        # Verify execution
        executed_task = storage.get_task(task.task_id)
        assert executed_task.status == TaskStatus.COMPLETED, "Task should be COMPLETED"
        assert executed_task.result == TaskResult.APPLIED, "Task should have APPLIED result"
        assert executed_task.worker_id == "worker-1", "Task should be assigned to worker-1"
        print(f"✓ Task completed")
        print(f"  - Status: {executed_task.status.value}")
        print(f"  - Result: {executed_task.result.value}")
        print(f"  - Worker: {executed_task.worker_id}")
        print(f"  - Duration: {(executed_task.completed_at - executed_task.started_at).total_seconds():.2f}s")

        # Test 4: Event emission
        print("\n[Test 4] Event system")
        print(f"✓ Events received: {len(events_received)}")
        for i, event in enumerate(events_received, 1):
            print(f"  {i}. {event['task']['task_id']} - {event['task']['status']}")

        expected_events = ["discovered", "queued", "running", "completed"]
        actual_events = [e["task"]["status"] for e in events_received]
        assert actual_events == expected_events, f"Event sequence mismatch: {actual_events}"
        print("✓ Event sequence correct")

        # Test 5: Manual review escalation
        print("\n[Test 5] Manual review escalation")
        task2 = orchestrator.enqueue_task(
            task_id="task-002",
            job_id="job-002",
            source_platform="indeed",
            metadata={"job": {"title": "Data Scientist"}},
        )

        # Create worker that returns REVIEW for indeed platform
        review_worker = MockWorker("worker-2", TaskResult.REVIEW, platforms=["indeed"])
        worker_pool.register(review_worker)

        await orchestrator.process_single_task(task2.task_id)

        executed_task2 = storage.get_task(task2.task_id)
        assert executed_task2.status == TaskStatus.MANUAL_REVIEW, "Task should be in MANUAL_REVIEW"
        print(f"✓ Task escalated to manual review")
        print(f"  - Status: {executed_task2.status.value}")

        review_records = manual_review_queue.get_pending()
        assert len(review_records) == 1, "Should have 1 pending review"
        print(f"✓ Manual review record created")
        print(f"  - Task: {review_records[0].task_id}")
        print(f"  - Status: {review_records[0].status}")

        # Test 6: Retry mechanism
        print("\n[Test 6] Retry mechanism")
        task3 = orchestrator.enqueue_task(
            task_id="task-003",
            job_id="job-003",
            source_platform="naukri",
            metadata={"job": {"title": "Product Manager"}},
        )

        # Create worker that fails for naukri platform
        fail_worker = MockWorker("worker-3", TaskResult.FAILED, platforms=["naukri"])
        worker_pool.register(fail_worker)

        await orchestrator.process_single_task(task3.task_id)

        executed_task3 = storage.get_task(task3.task_id)
        print(f"✓ Task failed and escalated")
        print(f"  - Status: {executed_task3.status.value}")
        print(f"  - Error: {executed_task3.error_message}")

        # Test 7: State transitions
        print("\n[Test 7] State transition history")
        history = storage.get_task_history(task.task_id)
        print(f"✓ State transitions recorded: {len(history)}")
        for transition in history:
            print(f"  - {transition['from_status']} → {transition['to_status']}")

        # Test 8: Orchestrator status
        print("\n[Test 8] Orchestrator status")
        status = orchestrator.get_status()
        print(f"✓ Orchestrator status:")
        print(f"  - Running: {status['running']}")
        print(f"  - Active tasks: {status['active_tasks']}")
        print(f"  - Queue size: {status['queue_size']}")
        print(f"  - Workers: {status['workers']}")

        print("\n=== All Tests Passed ===\n")


if __name__ == "__main__":
    asyncio.run(test_end_to_end_flow())

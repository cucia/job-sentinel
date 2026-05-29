# Phase 1 Runtime Quick Reference

## Initialization

```python
from backend.runtime.task_model import Task, TaskStatus, TaskResult
from backend.persistence.task_storage import TaskStorage
from backend.queue.queue import Queue
from backend.state.state_manager import StateManager
from backend.events.event_bus import EventBus
from backend.workers.browser_worker import WorkerPool, BrowserWorker
from backend.manual_review.review_queue import ManualReviewQueue
from backend.orchestrator.orchestrator import RuntimeOrchestrator

# Setup storage
storage = TaskStorage("data/jobsentinel.db")

# Setup event bus
event_bus = EventBus()

# Setup queue and state manager
queue = Queue(storage)
state_manager = StateManager(storage, event_bus)

# Setup workers
worker_pool = WorkerPool()
browser_worker = BrowserWorker(
    worker_id="browser-1",
    apply_functions=platforms,  # From existing code
    settings=settings,
    profile=profile,
    resume_path=resume_path,
)
worker_pool.register(browser_worker)

# Setup manual review
manual_review_queue = ManualReviewQueue(storage)

# Setup orchestrator
orchestrator = RuntimeOrchestrator(
    queue=queue,
    state_manager=state_manager,
    worker_pool=worker_pool,
    manual_review_queue=manual_review_queue,
    max_concurrent_tasks=5,
)
```

## Creating and Enqueueing Tasks

```python
# Create task from discovered job
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
            "description": "...",
        }
    },
)

print(f"Task created: {task.task_id}")
print(f"Status: {task.status.value}")
```

## Running the Orchestrator

```python
import asyncio

# Run orchestrator event loop
asyncio.run(orchestrator.start())

# Or process single task (for testing)
task = await orchestrator.process_single_task("task-001")
```

## Subscribing to Events

```python
def on_task_completed(data):
    task = data["task"]
    print(f"Task {task['task_id']} completed with result {task['result']}")

event_bus.subscribe("TASK_COMPLETED", on_task_completed)
event_bus.subscribe("MANUAL_REVIEW_REQUIRED", on_manual_review)
```

## Checking Queue Status

```python
# Queue size
size = queue.get_queue_size()
print(f"Queued tasks: {size}")

# Peek at next task
next_task = queue.peek()
if next_task:
    print(f"Next task: {next_task.task_id}")

# Get failed tasks eligible for retry
failed = queue.get_failed_tasks()
print(f"Failed tasks: {len(failed)}")

# Get manual review tasks
reviews = queue.get_manual_review_tasks()
print(f"Manual reviews: {len(reviews)}")
```

## Handling Manual Reviews

```python
# Get pending reviews
pending = manual_review_queue.get_pending(limit=10)
for record in pending:
    print(f"Task {record.task_id}: {record.context}")

# Mark as reviewed
manual_review_queue.mark_reviewed(
    task_id="task-001",
    decision="approve",
    notes="Looks good, proceed with application",
)

# Get review stats
stats = manual_review_queue.get_review_stats()
print(f"Pending: {stats['pending']}, Reviewed: {stats['reviewed']}")
```

## Retrieving Task State

```python
# Get task by ID
task = state_manager.get_task("task-001")
print(f"Status: {task.status.value}")
print(f"Result: {task.result.value if task.result else 'N/A'}")
print(f"Retries: {task.retry_count}/{task.max_retries}")

# Get tasks by status
queued = state_manager.get_tasks_by_status(TaskStatus.QUEUED)
completed = state_manager.get_tasks_by_status(TaskStatus.COMPLETED)
failed = state_manager.get_tasks_by_status(TaskStatus.FAILED)

# Get state transition history
history = storage.get_task_history("task-001")
for transition in history:
    print(f"{transition['from_status']} → {transition['to_status']}")
```

## Orchestrator Status

```python
status = orchestrator.get_status()
print(f"Running: {status['running']}")
print(f"Active tasks: {status['active_tasks']}")
print(f"Queue size: {status['queue_size']}")
print(f"Workers: {status['workers']}")
```

## Creating Custom Workers

```python
from backend.workers.browser_worker import Worker

class CustomWorker(Worker):
    def can_handle(self, task: Task) -> bool:
        # Return True if this worker can execute the task
        return task.source_platform == "custom_platform"
    
    async def execute(self, task: Task) -> TaskResult:
        # Execute task and return result
        try:
            # Do work
            return TaskResult.APPLIED
        except Exception as e:
            raise

# Register custom worker
custom_worker = CustomWorker("custom-1")
worker_pool.register(custom_worker)
```

## Event Types

```python
from backend.events.event_bus import EventType

# Available events
EventType.TASK_CREATED              # Task created
EventType.TASK_QUEUED               # Task queued
EventType.TASK_STARTED              # Task execution started
EventType.TASK_COMPLETED            # Task completed
EventType.TASK_FAILED               # Task failed
EventType.TASK_RETRIED              # Task retried
EventType.MANUAL_REVIEW_REQUIRED    # Escalated to manual review
EventType.WORKER_ASSIGNED           # Worker assigned
EventType.WORKER_RELEASED           # Worker released
```

## Task States

```python
from backend.runtime.task_model import TaskStatus

TaskStatus.DISCOVERED       # Initial state after creation
TaskStatus.QUEUED           # Ready for execution
TaskStatus.RUNNING          # Currently executing
TaskStatus.WAITING          # Waiting for something
TaskStatus.MANUAL_REVIEW    # Escalated for human review
TaskStatus.COMPLETED        # Successfully completed
TaskStatus.FAILED           # Execution failed
```

## Task Results

```python
from backend.runtime.task_model import TaskResult

TaskResult.APPLIED          # Successfully applied
TaskResult.REVIEW           # Requires manual review
TaskResult.SKIPPED          # Skipped (not applicable)
TaskResult.DEFERRED         # Deferred for later
TaskResult.FAILED           # Execution failed
```

## Integration with Existing Code

### From Controller

```python
# Old way (controller.py)
result = apply_fn(job, resume_path, settings)

# New way (runtime)
task = orchestrator.enqueue_task(
    task_id=job_key,
    job_id=job_key,
    source_platform=job["platform"],
    metadata={"job": job},
)
# Orchestrator handles execution asynchronously
```

### From Collectors

```python
# Collectors return jobs as before
jobs = collect_linkedin(settings, profile)

# Convert to tasks
for job in jobs:
    orchestrator.enqueue_task(
        task_id=_make_job_key(job),
        job_id=_make_job_key(job),
        source_platform="linkedin",
        metadata={"job": job},
    )
```

### From Dashboard

```python
# Subscribe to events for real-time updates
event_bus.subscribe("TASK_COMPLETED", lambda data: emit_websocket_update(data))
event_bus.subscribe("MANUAL_REVIEW_REQUIRED", lambda data: emit_review_notification(data))

# Query status
status = orchestrator.get_status()
reviews = manual_review_queue.get_pending()
```

## Common Patterns

### Process All Queued Tasks

```python
async def process_all():
    while True:
        size = queue.get_queue_size()
        if size == 0:
            break
        await orchestrator._process_batch()
        await asyncio.sleep(1)
```

### Retry Failed Tasks

```python
failed = queue.get_failed_tasks()
for task in failed:
    queue.retry(task)
```

### Export Manual Reviews

```python
reviews = manual_review_queue.get_pending()
for record in reviews:
    print(f"{record.task_id},{record.job_id},{record.context}")
```

### Monitor Execution

```python
def log_event(data):
    task = data["task"]
    print(f"[{task['status']}] {task['task_id']}")

event_bus.subscribe("TASK_CREATED", log_event)
event_bus.subscribe("TASK_STARTED", log_event)
event_bus.subscribe("TASK_COMPLETED", log_event)
event_bus.subscribe("TASK_FAILED", log_event)
```


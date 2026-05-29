# Phase 1 Runtime Bridge - Integration Examples

## Overview

The `RuntimeBridge` module provides a clean interface to integrate the new Phase 1 runtime with existing controller code. It handles initialization and provides simple methods for common operations.

---

## Basic Usage

### Initialize Bridge

```python
from backend.bridge import create_runtime_bridge
from src.core.config import load_settings, load_profile
from src.core.platform_registry import get_platforms

base_dir = "/path/to/jobsentinel"
settings = load_settings(base_dir)
profile = load_profile(base_dir)
platforms = get_platforms()

bridge = create_runtime_bridge(base_dir, settings, profile, platforms)
```

### Enqueue Jobs

```python
# Single job
task_id = bridge.enqueue_job(job, priority=10)

# Multiple jobs
jobs = collect_linkedin(settings, profile)
task_ids = bridge.enqueue_jobs(jobs, priority=5)
```

### Check Queue Status

```python
queue_size = bridge.get_queue_size()
print(f"Queued tasks: {queue_size}")

status = bridge.get_orchestrator_status()
print(f"Active: {status['active_tasks']}, Queue: {status['queue_size']}")
```

### Handle Manual Reviews

```python
# Get pending reviews
reviews = bridge.get_pending_reviews(limit=20)
for review in reviews:
    print(f"Task {review['task_id']}: {review['context']}")

# Get stats
stats = bridge.get_review_stats()
print(f"Pending: {stats['pending']}, Reviewed: {stats['reviewed']}")
```

---

## Integration with Controller

### Refactored Collection Phase

```python
# Old controller.py (Phase 0)
def _run_queue_cycle(...):
    jobs = collect_jobs(settings, profile)
    for job in jobs:
        enqueue_job(db_path, job)  # Direct DB write

# New controller.py (Phase 1)
def _run_queue_cycle(...):
    bridge = create_runtime_bridge(base_dir, settings, profile, platforms)
    jobs = collect_jobs(settings, profile)
    bridge.enqueue_jobs(jobs, priority=0)
    # Orchestrator handles execution asynchronously
```

### Refactored Application Phase

```python
# Old controller.py (Phase 0)
def _run_queue_cycle(...):
    while True:
        job = next_queued_job(db_path)
        if not job:
            break
        result = apply_fn(job, resume_path, settings)
        update_job(db_path, job["job_key"], status=result)

# New controller.py (Phase 1)
# No application phase needed - orchestrator handles it
# Just enqueue jobs and let runtime execute
```

---

## Event Monitoring

### Subscribe to Events

```python
def on_task_completed(data):
    task = data["task"]
    print(f"✓ Applied: {task['job_id']}")

def on_manual_review(data):
    task = data["task"]
    print(f"⚠ Review needed: {task['job_id']}")

bridge.subscribe_to_events("TASK_COMPLETED", on_task_completed)
bridge.subscribe_to_events("MANUAL_REVIEW_REQUIRED", on_manual_review)
```

### Get Event History

```python
# All events
all_events = bridge.get_event_history(limit=100)

# Specific event type
completed = bridge.get_event_history("TASK_COMPLETED", limit=50)

for event in completed:
    print(f"{event['event_type']}: {event['data']['task']['task_id']}")
```

---

## Dashboard Integration

### Real-Time Status

```python
# In dashboard route handler
@app.route("/api/runtime/status")
def get_runtime_status():
    status = bridge.get_orchestrator_status()
    reviews = bridge.get_pending_reviews(limit=10)
    return {
        "orchestrator": status,
        "pending_reviews": reviews,
        "review_stats": bridge.get_review_stats(),
    }
```

### WebSocket Updates

```python
# In WebSocket handler
def on_connect():
    def emit_status():
        status = bridge.get_orchestrator_status()
        socketio.emit("runtime_status", status)
    
    bridge.subscribe_to_events("TASK_COMPLETED", lambda d: emit_status())
    bridge.subscribe_to_events("TASK_FAILED", lambda d: emit_status())
```

---

## CLI Integration

### List Queued Tasks

```python
# In review.py
def list_queued():
    bridge = create_runtime_bridge(base_dir, settings, profile, platforms)
    size = bridge.get_queue_size()
    print(f"Queued tasks: {size}")
    
    status = bridge.get_orchestrator_status()
    print(f"Active: {status['active_tasks']}")
```

### List Manual Reviews

```python
# In review.py
def list_reviews():
    bridge = create_runtime_bridge(base_dir, settings, profile, platforms)
    reviews = bridge.get_pending_reviews(limit=20)
    
    for review in reviews:
        print(f"{review['task_id']} | {review['job_id']} | {review['status']}")
```

---

## Monitoring and Logging

### Setup Logging

```python
import logging

logger = logging.getLogger("jobsentinel.runtime")

def log_task_event(data):
    task = data["task"]
    logger.info(f"Task {task['task_id']}: {task['status']}")

bridge.subscribe_to_events("TASK_CREATED", log_task_event)
bridge.subscribe_to_events("TASK_COMPLETED", log_task_event)
bridge.subscribe_to_events("TASK_FAILED", log_task_event)
```

### Metrics Collection

```python
from prometheus_client import Counter

tasks_completed = Counter("jobsentinel_tasks_completed", "Tasks completed")
tasks_failed = Counter("jobsentinel_tasks_failed", "Tasks failed")
tasks_reviewed = Counter("jobsentinel_tasks_reviewed", "Tasks in manual review")

def on_completed(data):
    tasks_completed.inc()

def on_failed(data):
    tasks_failed.inc()

def on_review(data):
    tasks_reviewed.inc()

bridge.subscribe_to_events("TASK_COMPLETED", on_completed)
bridge.subscribe_to_events("TASK_FAILED", on_failed)
bridge.subscribe_to_events("MANUAL_REVIEW_REQUIRED", on_review)
```

---

## Error Handling

### Graceful Degradation

```python
try:
    bridge = create_runtime_bridge(base_dir, settings, profile, platforms)
    bridge.enqueue_jobs(jobs)
except Exception as e:
    log(f"Runtime bridge error: {e}")
    # Fallback to direct execution if needed
    for job in jobs:
        result = apply_fn(job, resume_path, settings)
```

### Task Status Checking

```python
task_id = bridge.enqueue_job(job)

# Check status later
task_status = bridge.get_task_status(task_id)
if task_status:
    print(f"Status: {task_status['status']}")
    if task_status['status'] == 'failed':
        print(f"Error: {task_status['error_message']}")
else:
    print("Task not found")
```

---

## Migration Path

### Phase 1a: Parallel Execution

Run both old and new systems in parallel:

```python
def run_cycle():
    # Old system
    _run_queue_cycle(...)
    
    # New system (parallel)
    bridge = create_runtime_bridge(...)
    bridge.enqueue_jobs(jobs)
```

### Phase 1b: Gradual Cutover

Use feature flag to switch:

```python
def run_cycle():
    use_runtime = settings.get("app", {}).get("use_runtime", False)
    
    if use_runtime:
        bridge = create_runtime_bridge(...)
        bridge.enqueue_jobs(jobs)
    else:
        _run_queue_cycle(...)  # Old system
```

### Phase 1c: Full Migration

Remove old system, use runtime exclusively:

```python
def run_cycle():
    bridge = create_runtime_bridge(...)
    jobs = collect_jobs(settings, profile)
    bridge.enqueue_jobs(jobs)
    # Done - orchestrator handles execution
```

---

## API Reference

### RuntimeBridge Methods

```python
# Initialization
bridge = create_runtime_bridge(base_dir, settings, profile, platforms)

# Job enqueueing
task_id = bridge.enqueue_job(job, priority=0)
task_ids = bridge.enqueue_jobs(jobs, priority=0)

# Queue status
size = bridge.get_queue_size()
status = bridge.get_orchestrator_status()

# Manual reviews
reviews = bridge.get_pending_reviews(limit=100)
stats = bridge.get_review_stats()

# Task status
task = bridge.get_task_status(task_id)

# Events
bridge.subscribe_to_events(event_type, handler)
history = bridge.get_event_history(event_type=None, limit=100)
```

### Event Types

```
TASK_CREATED
TASK_QUEUED
TASK_STARTED
TASK_COMPLETED
TASK_FAILED
TASK_RETRIED
MANUAL_REVIEW_REQUIRED
WORKER_ASSIGNED
WORKER_RELEASED
```

---

## Summary

The `RuntimeBridge` provides a simple, clean interface to integrate Phase 1 runtime with existing code. It handles all initialization and provides methods for common operations.

Key benefits:
- ✅ Non-destructive integration
- ✅ Backward compatible
- ✅ Gradual migration path
- ✅ Event-driven monitoring
- ✅ Simple API


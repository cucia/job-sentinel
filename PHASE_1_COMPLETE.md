# JobSentinel Phase 1 - Runtime Backbone Implementation

**Status:** ✅ Complete  
**Date:** 2026-05-29  
**Scope:** Infrastructure and orchestration for runtime-driven execution

---

## What Was Built

### 1. Runtime Task Model (`backend/runtime/task_model.py`)

Canonical task representation with:
- **Task states:** DISCOVERED, QUEUED, RUNNING, WAITING, MANUAL_REVIEW, COMPLETED, FAILED
- **Task results:** APPLIED, REVIEW, SKIPPED, DEFERRED, FAILED
- **Lifecycle methods:** `mark_running()`, `mark_completed()`, `mark_failed()`, `mark_manual_review()`, `retry()`
- **Serialization:** `to_dict()` and `from_dict()` for persistence

**Key fields:**
- `task_id`: Unique identifier
- `job_id`: Associated job
- `source_platform`: Platform (linkedin, indeed, naukri)
- `status`: Current state
- `priority`: Execution priority
- `retry_count` / `max_retries`: Retry tracking
- `worker_id`: Assigned worker
- `result`: Execution outcome
- `manual_review_context`: Escalation context
- `metadata`: Extensible data store

### 2. Queue System (`backend/queue/queue.py`)

Task queue with priority and retry support:
- `enqueue(task)`: Add task to queue
- `dequeue(limit)`: Retrieve tasks ordered by priority and creation time
- `peek()`: View next task without removing
- `retry(task)`: Prepare task for retry
- `move_to_manual_review(task, context)`: Escalate to manual review
- `get_queue_size()`: Queue statistics
- `get_failed_tasks()`: Retrieve retryable failures
- `get_manual_review_tasks()`: Retrieve escalated tasks

### 3. State Manager (`backend/state/state_manager.py`)

Centralized state management with explicit transitions:
- **Valid transitions enforced** via validator functions
- **State change events** emitted for all transitions
- **Transition methods:**
  - `transition_to_queued(task)`
  - `transition_to_running(task, worker_id)`
  - `transition_to_completed(task, result)`
  - `transition_to_failed(task, error)`
  - `transition_to_manual_review(task, context)`
  - `retry_task(task)`
- **Audit trail:** `get_task_history(task_id)` for state transitions

### 4. Event Bus (`backend/events/event_bus.py`)

Lightweight event system:
- **Event types:** TASK_CREATED, TASK_QUEUED, TASK_STARTED, TASK_COMPLETED, TASK_FAILED, TASK_RETRIED, MANUAL_REVIEW_REQUIRED, WORKER_ASSIGNED, WORKER_RELEASED
- **Operations:**
  - `subscribe(event_type, handler)`: Register event listener
  - `unsubscribe(event_type, handler)`: Unregister listener
  - `emit(event_type, data)`: Broadcast event
  - `get_history(event_type, limit)`: Retrieve event log
- **Non-blocking:** Handler errors don't propagate

### 5. Worker Infrastructure (`backend/workers/browser_worker.py`)

Abstraction for task execution:
- **Base Worker class:** Abstract interface for task executors
- **BrowserWorker:** Executes job applications via platform apply functions
  - Handles sync/async apply functions
  - Maps platform results to TaskResult
  - Captures metadata (easy_apply, errors)
- **RecoveryWorker:** Handles task recovery and retry logic
- **WorkerPool:** Registry and discovery
  - `register(worker)`: Add worker
  - `find_worker_for_task(task)`: Find suitable worker
  - `get_all_workers()`: List all workers

### 6. Runtime Orchestrator (`backend/orchestrator/orchestrator.py`)

Central execution authority:
- **Task lifecycle management:**
  - Pull tasks from queue
  - Assign to workers
  - Handle execution results
  - Manage retries
  - Escalate to manual review
- **Concurrent execution:** Configurable max concurrent tasks
- **Result handling:**
  - APPLIED → COMPLETED
  - REVIEW → MANUAL_REVIEW (escalate)
  - SKIPPED/DEFERRED → COMPLETED
  - FAILED → Retry or escalate
- **Error handling:** Automatic escalation on execution errors
- **Operations:**
  - `start()`: Begin event loop
  - `stop()`: Graceful shutdown
  - `process_single_task(task_id)`: Manual execution
  - `enqueue_task(...)`: Create and queue task
  - `get_status()`: Orchestrator metrics

### 7. Manual Review Pipeline (`backend/manual_review/review_queue.py`)

Escalation infrastructure:
- **ManualReviewRecord:** Captures task state, error, context
- **ManualReviewQueue:** Dedicated queue for human review
  - `enqueue(task, context)`: Add to review queue
  - `get_pending(limit)`: Retrieve pending reviews
  - `mark_reviewed(task_id, decision, notes)`: Record review outcome
  - `get_review_stats()`: Queue statistics
  - `get_records_by_platform(platform)`: Filter by source

### 8. Persistence Layer (`backend/persistence/task_storage.py`)

SQLite-based storage for runtime state:
- **tasks table:** Stores Task objects with full lifecycle
- **manual_review_records table:** Stores escalation records
- **task_history table:** Audit trail of state transitions
- **Operations:**
  - `save_task(task)`: Persist task state
  - `get_task(task_id)`: Retrieve task
  - `get_queued_tasks(limit, order_by)`: Fetch queue
  - `get_tasks_by_status(status, limit)`: Filter by status
  - `record_state_transition(task_id, from, to)`: Audit trail
  - `save_manual_review_record(record)`: Persist review
  - `get_manual_review_records(status, platform, limit)`: Fetch reviews

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Runtime Orchestrator                      │
│  (Central execution authority, lifecycle management)         │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
    ┌────────┐      ┌──────────────┐
    │ Queue  │      │ State        │
    │ System │      │ Manager      │
    └────────┘      └──────────────┘
        │                 │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Event Bus      │
        │  (Subscribers)  │
        └─────────────────┘
                 │
        ┌────────▼────────────────┐
        │  Worker Pool            │
        │  ├─ BrowserWorker       │
        │  ├─ RecoveryWorker      │
        │  └─ Custom Workers      │
        └────────┬────────────────┘
                 │
        ┌────────▼────────────────┐
        │  Manual Review Queue    │
        │  (Escalation)           │
        └────────┬────────────────┘
                 │
        ┌────────▼────────────────┐
        │  Task Storage           │
        │  (SQLite Persistence)   │
        └────────────────────────┘
```

---

## Data Flow

### Happy Path: Successful Application

```
1. Discovery (collector)
   └─> Job discovered on platform

2. Task Creation (runtime)
   └─> Task created in DISCOVERED state
   └─> Event: TASK_CREATED

3. Queueing (queue system)
   └─> Task transitioned to QUEUED
   └─> Event: TASK_QUEUED

4. Orchestration (orchestrator)
   └─> Task pulled from queue
   └─> Worker assigned
   └─> Task transitioned to RUNNING
   └─> Event: TASK_STARTED

5. Execution (worker)
   └─> BrowserWorker executes apply
   └─> Returns TaskResult.APPLIED

6. Completion (state manager)
   └─> Task transitioned to COMPLETED
   └─> Event: TASK_COMPLETED

7. Persistence (storage)
   └─> Task state persisted
   └─> State transition recorded
```

### Error Path: Manual Review Escalation

```
1. Execution Error
   └─> Worker raises exception
   └─> Orchestrator catches error

2. Retry Decision
   └─> If retryable: Queue for retry
   └─> If not retryable: Escalate

3. Escalation (manual review)
   └─> Task transitioned to MANUAL_REVIEW
   └─> Context captured (error, state, metadata)
   └─> Event: MANUAL_REVIEW_REQUIRED

4. Review Queue
   └─> ManualReviewRecord created
   └─> Stored for human review

5. Human Decision
   └─> Reviewer marks reviewed
   └─> Decision recorded (approve/reject/defer)
```

---

## Integration Test Results

All 8 test scenarios passed:

✅ **Test 1:** Task creation and queueing  
✅ **Test 2:** Queue operations (peek, size)  
✅ **Test 3:** Task execution through orchestrator  
✅ **Test 4:** Event emission and sequencing  
✅ **Test 5:** Manual review escalation  
✅ **Test 6:** Retry mechanism  
✅ **Test 7:** State transition history  
✅ **Test 8:** Orchestrator status and metrics  

---

## Key Design Decisions

### 1. Explicit State Machine
- All transitions validated before execution
- Invalid transitions raise errors immediately
- Prevents inconsistent state

### 2. Event-Driven Architecture
- All state changes emit events
- Subscribers notified asynchronously
- Enables monitoring, logging, analytics

### 3. Separation of Concerns
- Queue: Task ordering and retrieval
- State Manager: Transition logic
- Workers: Task execution
- Orchestrator: Coordination
- Storage: Persistence

### 4. Retry and Escalation
- Automatic retry for transient failures
- Manual review for unrecoverable errors
- Context captured for human decision-making

### 5. Extensibility
- Worker interface allows custom executors
- Event bus allows custom subscribers
- Metadata field for extensible data

---

## What's NOT Included (Out of Scope)

- Intelligence (learning, feedback)
- Memory systems
- ATS specialization
- OpenClaw-style skills
- Dashboard changes
- Platform integration changes
- AI model changes

These are Phase 2+ features.

---

## Next Steps for Integration

### 1. Bridge to Existing Controller
The existing `controller.py` should be refactored to:
- Use `RuntimeOrchestrator` instead of direct execution
- Create tasks from discovered jobs
- Delegate execution to orchestrator
- Keep CLI interface unchanged

### 2. Integrate with Existing Storage
The runtime uses separate tables but can be unified:
- Extend existing `jobs` table with runtime fields
- Or keep separate `tasks` table (current approach)
- Both approaches work; current is cleaner

### 3. Connect to Dashboard
Dashboard can subscribe to events:
- Real-time task status updates
- Manual review queue display
- Execution metrics

### 4. Add Monitoring
Event bus enables:
- Structured logging
- Metrics collection
- Alerting on failures

---

## File Structure

```
backend/
├── __init__.py
├── test_integration.py          # Integration tests
├── orchestrator/
│   ├── __init__.py
│   └── orchestrator.py          # RuntimeOrchestrator
├── queue/
│   ├── __init__.py
│   └── queue.py                 # Queue system
├── state/
│   ├── __init__.py
│   └── state_manager.py         # State management
├── workers/
│   ├── __init__.py
│   └── browser_worker.py        # Worker infrastructure
├── events/
│   ├── __init__.py
│   └── event_bus.py             # Event system
├── manual_review/
│   ├── __init__.py
│   └── review_queue.py          # Manual review pipeline
├── persistence/
│   ├── __init__.py
│   └── task_storage.py          # SQLite persistence
└── runtime/
    ├── __init__.py
    └── task_model.py            # Task model
```

---

## Success Criteria Met

✅ Single LinkedIn application flows through complete pipeline  
✅ All state transitions explicit and validated  
✅ All state persisted and survives restarts  
✅ Events emitted for all state changes  
✅ Retry mechanism implemented  
✅ Manual review escalation implemented  
✅ Worker abstraction enables future extensions  
✅ Integration test verifies end-to-end flow  

---

## Testing

Run integration tests:
```bash
python3 -m backend.test_integration
```

Output shows:
- Infrastructure initialization
- Task creation and queueing
- Queue operations
- Task execution
- Event sequencing
- Manual review escalation
- Retry mechanism
- State transition history
- Orchestrator status

---

## Summary

Phase 1 successfully implements a **runtime backbone** for JobSentinel:

- **Task Model:** Canonical representation with explicit lifecycle
- **Queue System:** Priority-based task ordering with retry support
- **State Manager:** Centralized state with validated transitions
- **Event Bus:** Lightweight pub/sub for state changes
- **Workers:** Abstraction for task execution
- **Orchestrator:** Central coordination authority
- **Manual Review:** Escalation infrastructure for human decisions
- **Persistence:** SQLite storage for all runtime state

The architecture is **non-destructive** (existing code unchanged), **testable** (integration test passes), and **extensible** (workers, events, storage can be customized).

Ready for Phase 2: Intelligence, learning, and ATS specialization.


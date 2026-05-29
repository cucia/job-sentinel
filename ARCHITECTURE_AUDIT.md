# JobSentinel Architecture Audit

**Date:** 2026-05-29  
**Scope:** Phase 1 Runtime Backbone Migration  
**Status:** Pre-implementation audit

---

## Executive Summary

JobSentinel is a mature job application automation system with:
- **3 platform integrations** (LinkedIn, Indeed, Naukri)
- **Multi-stage AI filtering pipeline** (scoring, quality, visibility, diversity)
- **Controller-driven execution** (monolithic orchestration)
- **SQLite persistence** with job tracking and feedback learning
- **Dashboard UI** with WebSocket support
- **Browser automation** via Playwright

Current architecture is **controller-centric**: `controller.py` owns discovery, filtering, queueing, and application execution. Phase 1 must extract runtime responsibilities into dedicated infrastructure without breaking existing functionality.

---

## Component Classification

### KEEP (No Changes Required)

| Component | Location | Reason |
|-----------|----------|--------|
| Platform Integrations | `src/platforms/{linkedin,indeed,naukri}/` | Stable, working collectors and apply modules |
| AI Scoring Pipeline | `src/ai/scorer.py` | Core decision logic, reusable |
| Quality Filtering | `src/ai/quality_scorer.py`, `adaptive_strategy.py` | Specialized filtering, keep as-is |
| Browser Automation | `src/core/browser.py` | Anti-detection setup, working |
| Session Management | `src/services/session_manager.py` | Session persistence, working |
| Dashboard UI | `dashboard/` | Frontend, independent of runtime |
| Storage Layer | `src/core/storage.py` | SQLite schema, working |
| Config System | `src/core/config.py` | YAML-based config, working |

### REFACTOR (Extract Responsibilities)

| Component | Location | Current Role | Target Role |
|-----------|----------|--------------|------------|
| controller.py | `src/core/controller.py` | Monolithic orchestrator | Thin CLI wrapper |
| Job Queueing | Embedded in controller | Ad-hoc queue ops | Dedicated queue system |
| State Management | Scattered in controller | Implicit state transitions | Centralized state layer |
| Execution Flow | Embedded in controller | Direct apply calls | Runtime orchestrator |
| Event Tracking | Logging only | No event system | Event bus |

### REPLACE (New Systems)

| Component | Purpose | Scope |
|-----------|---------|-------|
| Runtime Task Model | Canonical task representation | task_id, status, retry_count, etc. |
| Queue System | Task queueing and dequeuing | enqueue, dequeue, retry operations |
| Shared State Layer | Centralized runtime state | Task progress, worker assignments |
| Runtime Orchestrator | Central execution authority | Pull tasks, assign workers, manage lifecycle |
| Worker Infrastructure | Task execution | BrowserWorker, RecoveryWorker |
| Event System | Lightweight event bus | emit, subscribe, event types |
| Manual Review Pipeline | Escalation infrastructure | Capture state, store context |

---

## Current Execution Flow

### Phase 1: Collection & Filtering (controller.py:358-558)

```
collect_jobs()
  ├─ LinkedIn collector
  ├─ Indeed collector
  └─ Naukri collector
       ↓
For each job:
  ├─ Check if seen (has_seen_job)
  ├─ Enqueue (enqueue_job → status='queued')
  ├─ Enrich if needed
  ├─ Entry-level filter
  ├─ Policy filter
  ├─ AI filter (score, quality, visibility, diversity)
  └─ Update status (queued → skipped/review/queued)
```

**Current Issues:**
- All filtering logic in one function (622 lines)
- State transitions implicit in conditional branches
- No event emission
- No retry mechanism
- No manual review escalation

### Phase 2: Application (controller.py:560-619)

```
while next_queued_job():
  ├─ Get apply function for platform
  ├─ Call apply_fn(job, resume_path, settings)
  ├─ Handle result (applied/review/skipped/deferred)
  └─ Update job status
```

**Current Issues:**
- Synchronous, blocking loop
- No worker abstraction
- No retry on failure
- Exception → manual review (implicit)
- No task lifecycle tracking

### Direct Latest Cycle (controller.py:622-911)

Alternative pipeline that:
- Selects latest N jobs
- Applies AI filtering
- Ranks candidates
- Splits into easy-apply and standard lanes
- Runs async apply lanes

**Current Issues:**
- Duplicate filtering logic
- Async/sync mixing
- No unified task model

---

## Storage Schema

### jobs table
```sql
job_key (UNIQUE)
platform, title, company, location, description, job_url
status (queued, applied, review, skipped, deferred, rejected)
easy_apply (0/1)
score (int)
decision (string)
posted_at, posted_text
created_at, updated_at, applied_at
```

**Observations:**
- No task_id (uses job_key as identifier)
- No retry_count
- No worker assignment
- No manual_review_context
- Status field is the only state indicator

### feedback table
```sql
job_key (PRIMARY KEY)
label (approved, rejected, positive, negative, skipped)
notes, source
created_at, updated_at
```

### model_state table
```sql
name (PRIMARY KEY)
weights_json, bias, trained_examples
updated_at
```

---

## Key Observations

### 1. Queue Exists But Is Implicit
- `enqueue_job()` sets status='queued'
- `next_queued_job()` fetches first queued job
- No queue abstraction, no priority, no retry tracking

### 2. State Transitions Are Scattered
- Status updates happen in multiple places
- No centralized state machine
- Implicit transitions (e.g., exception → review)

### 3. No Task Lifecycle
- Jobs don't have task_id
- No way to track a job through multiple retries
- No manual review context capture

### 4. Worker Execution Is Synchronous
- Phase 2 is a blocking while loop
- Direct latest cycle has async lanes but no worker abstraction
- No worker pool, no concurrency control

### 5. Manual Review Is Implicit
- Exceptions → status='review'
- No context capture
- No escalation infrastructure

### 6. Event System Missing
- Only logging (no structured events)
- No subscribers
- No event replay

---

## Phase 1 Implementation Strategy

### Step 1: Create Runtime Task Model
- Add task_id to jobs table (or create tasks table)
- Add retry_count, worker_id, manual_review_context
- Define task states: DISCOVERED, QUEUED, RUNNING, WAITING, MANUAL_REVIEW, COMPLETED, FAILED

### Step 2: Build Queue System
- Create `backend/queue/queue.py` with enqueue, dequeue, retry operations
- Reuse existing storage layer
- Support priority, retry limits

### Step 3: Implement Shared State Layer
- Create `backend/state/state_manager.py`
- Centralize task state transitions
- Persist state to storage

### Step 4: Build Runtime Orchestrator
- Create `backend/orchestrator/orchestrator.py`
- Pull tasks from queue
- Assign to workers
- Manage lifecycle and retries
- Escalate to manual review

### Step 5: Create Worker Infrastructure
- Create `backend/workers/browser_worker.py` (executes apply)
- Create `backend/workers/recovery_worker.py` (handles failures)
- Workers are stateless, receive tasks from orchestrator

### Step 6: Implement Event System
- Create `backend/events/event_bus.py`
- Support emit, subscribe
- Event types: TASK_CREATED, TASK_STARTED, TASK_COMPLETED, TASK_FAILED, MANUAL_REVIEW_REQUIRED

### Step 7: Build Manual Review Pipeline
- Create `backend/manual_review/review_queue.py`
- Capture state and context
- Store for human review

### Step 8: Migrate Controller
- Extract queue management → runtime
- Extract state management → runtime
- Extract lifecycle management → runtime
- Keep CLI interface, reduce to thin wrapper

---

## Success Criteria

A single LinkedIn application should flow:

```
Discovery (collector)
  ↓
Task Creation (runtime)
  ↓
Queue (queue system)
  ↓
Orchestrator (pulls task)
  ↓
Browser Worker (executes apply)
  ↓
State Update (state manager)
  ↓
Completion OR Manual Review
```

All state transitions must be:
- Explicit (state machine)
- Persistent (survives restart)
- Observable (events)
- Recoverable (retry mechanism)

---

## Out of Scope (Phase 1)

- Intelligence (learning, feedback)
- Memory systems
- ATS specialization
- OpenClaw-style skills
- Dashboard changes
- Platform integration changes
- AI model changes

---

## File Structure After Phase 1

```
src/
├── core/
│   ├── controller.py (REFACTORED: thin wrapper)
│   ├── storage.py (KEEP)
│   ├── config.py (KEEP)
│   ├── browser.py (KEEP)
│   └── ...
├── platforms/ (KEEP)
├── ai/ (KEEP)
└── services/ (KEEP)

backend/
├── __init__.py
├── orchestrator/
│   ├── __init__.py
│   └── orchestrator.py
├── queue/
│   ├── __init__.py
│   └── queue.py
├── state/
│   ├── __init__.py
│   └── state_manager.py
├── workers/
│   ├── __init__.py
│   ├── browser_worker.py
│   └── recovery_worker.py
├── events/
│   ├── __init__.py
│   └── event_bus.py
├── manual_review/
│   ├── __init__.py
│   └── review_queue.py
├── persistence/
│   ├── __init__.py
│   └── task_storage.py
└── runtime/
    ├── __init__.py
    └── task_model.py
```

---

## Migration Path

1. **Create backend/ directory structure** (non-destructive)
2. **Implement task model** (new code, no changes to existing)
3. **Implement queue system** (new code, wraps existing storage)
4. **Implement state manager** (new code, wraps existing storage)
5. **Implement orchestrator** (new code, coordinates workers)
6. **Implement workers** (new code, wraps existing apply functions)
7. **Implement event bus** (new code, optional subscribers)
8. **Implement manual review** (new code, new storage)
9. **Refactor controller** (extract responsibilities, keep CLI)
10. **Test end-to-end** (single job through full pipeline)

All changes are **additive** until step 9. No existing code is deleted or modified until the new runtime is proven.

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Breaking existing collectors | Keep platform code unchanged |
| Breaking existing storage | New code wraps existing storage layer |
| Breaking dashboard | Dashboard is independent |
| Breaking AI pipeline | AI code unchanged, only orchestration changes |
| Data loss | All state persisted to existing DB |
| Incomplete migration | Incremental extraction, test at each step |

---

## Next Steps

1. Create `backend/` directory structure
2. Implement `backend/runtime/task_model.py`
3. Implement `backend/queue/queue.py`
4. Implement `backend/state/state_manager.py`
5. Implement `backend/orchestrator/orchestrator.py`
6. Implement `backend/workers/browser_worker.py`
7. Implement `backend/events/event_bus.py`
8. Implement `backend/manual_review/review_queue.py`
9. Create integration test (single job end-to-end)
10. Refactor controller to use new runtime


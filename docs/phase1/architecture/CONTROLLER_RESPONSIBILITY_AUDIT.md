# Controller.py Responsibility Audit - Phase 1 Finalization

**Date:** 2026-05-29  
**Scope:** Identify controller responsibilities for runtime architecture  
**Goal:** Reduce controller ownership to focus on discovery only

---

## Current Controller Responsibilities

### 1. Utility Functions (Lines 39-138)

| Function | Purpose | Current Owner | Should Be | Reason |
|---|---|---|---|---|
| `_base_dir()` | Get base directory | controller | Shared utility | Used by multiple modules |
| `_resolve_db_path()` | Resolve DB path | controller | Shared utility | Used by scheduler, runtime |
| `_make_job_key()` | Create job identifier | controller | Shared utility | Used by discovery, storage |
| `_is_entry_level()` | Filter by seniority | controller | Discovery filter | Job filtering logic |
| `_parse_posted_at()` | Parse timestamp | controller | Shared utility | Date parsing |
| `_relative_posted_minutes()` | Parse relative time | controller | Shared utility | Date parsing |
| `_job_sort_key()` | Sort jobs by recency | controller | Discovery filter | Job ranking |
| `_select_latest_jobs()` | Select top N jobs | controller | Discovery filter | Job selection |
| `_merge_existing_job()` | Merge job data | controller | Storage layer | Data merging |
| `_rank_apply_candidates()` | Rank candidates | controller | Orchestrator | Execution ranking |

### 2. Job Collection (Lines 326-355)

| Function | Purpose | Current Owner | Should Be | Reason |
|---|---|---|---|---|
| `collect_jobs()` | Collect from all platforms | controller | Discovery | Core discovery responsibility |

**Status:** ✅ KEEP in controller (core discovery)

### 3. Queue Cycle (Lines 358-619)

| Function | Purpose | Current Owner | Should Be | Reason |
|---|---|---|---|---|
| `_run_queue_cycle()` | Queue-based pipeline | controller | Orchestrator | Execution orchestration |

**Responsibilities within:**
- Job collection ✅ KEEP
- Job enqueueing → Move to orchestrator
- Job filtering → Move to orchestrator
- Job application → Move to orchestrator

### 4. Direct Latest Cycle (Lines 622-911)

| Function | Purpose | Current Owner | Should Be | Reason |
|---|---|---|---|---|
| `_run_direct_latest_cycle()` | Direct latest pipeline | controller | Orchestrator | Execution orchestration |

**Responsibilities within:**
- Job collection ✅ KEEP
- Job ranking → Move to orchestrator
- Job application → Move to orchestrator

### 5. Direct Apply Lane (Lines 245-323)

| Function | Purpose | Current Owner | Should Be | Reason |
|---|---|---|---|---|
| `_apply_direct_candidate()` | Apply to single job | controller | Worker | Task execution |
| `_run_direct_apply_lane()` | Run apply lane | controller | Orchestrator | Lane orchestration |
| `_run_direct_apply_lanes()` | Run multiple lanes | controller | Orchestrator | Concurrent orchestration |

### 6. Entry Point (Lines 914-982)

| Function | Purpose | Current Owner | Should Be | Reason |
|---|---|---|---|---|
| `run_cycle()` | Execute cycle | controller | Scheduler | Cycle invocation |
| `main()` | Entry point | controller | Scheduler | Scheduling loop |

**Status:** ✅ MOVED to scheduler (already done)

---

## Responsibility Mapping

### KEEP in Controller (Discovery Only)

```
Controller Responsibilities (KEEP):
├─ collect_jobs()
│   ├─ Collect from LinkedIn
│   ├─ Collect from Indeed
│   └─ Collect from Naukri
└─ Utility functions
    ├─ _make_job_key()
    ├─ _parse_posted_at()
    ├─ _relative_posted_minutes()
    └─ _merge_existing_job()
```

### MOVE to Orchestrator (Execution)

```
Orchestrator Responsibilities (MOVE):
├─ Job filtering
│   ├─ Entry level filter
│   ├─ Policy filter
│   ├─ AI filter
│   ├─ Quality filter
│   ├─ Visibility filter
│   └─ Diversity filter
├─ Job ranking
│   ├─ _rank_apply_candidates()
│   ├─ _job_sort_key()
│   └─ _select_latest_jobs()
├─ Job application
│   ├─ _apply_direct_candidate()
│   ├─ _run_direct_apply_lane()
│   └─ _run_direct_apply_lanes()
└─ Pipeline orchestration
    ├─ _run_queue_cycle()
    └─ _run_direct_latest_cycle()
```

### MOVE to Shared Utilities

```
Shared Utilities (MOVE):
├─ _base_dir()
├─ _resolve_db_path()
├─ _is_entry_level()
├─ _parse_posted_at()
├─ _relative_posted_minutes()
└─ _merge_existing_job()
```

---

## Current vs Target Architecture

### Current (Controller-Centric)

```
controller.main()
  ├─ Load settings
  ├─ Parse args
  ├─ while True:
  │   ├─ run_cycle()
  │   │   ├─ collect_jobs()
  │   │   ├─ filter jobs
  │   │   ├─ rank jobs
  │   │   ├─ apply jobs
  │   │   └─ update state
  │   └─ sleep(interval)
```

**Lines of Code:** 983 lines  
**Responsibilities:** 15+  
**Concerns:** Mixed (scheduling, discovery, filtering, execution)

### Target (Scheduler-Driven)

```
scheduler.main()
  ├─ Create scheduler
  └─ scheduler.start()
      ├─ _initialize()
      └─ while running:
          ├─ _run_cycle()
          │   ├─ collect_jobs() [controller]
          │   └─ enqueue_jobs() [bridge]
          └─ sleep(interval)

orchestrator.start()
  └─ while running:
      ├─ dequeue_task()
      ├─ filter_task()
      ├─ rank_task()
      ├─ execute_task()
      └─ update_state()

controller.collect_jobs()
  ├─ Collect from LinkedIn
  ├─ Collect from Indeed
  └─ Collect from Naukri
```

**Controller Lines:** ~50 (discovery only)  
**Responsibilities:** 1 (discovery)  
**Concerns:** Single (job discovery)

---

## Refactoring Plan

### Phase 1: Extract Filtering Logic

**Move from controller to orchestrator:**
- Entry level filtering
- Policy filtering
- AI filtering
- Quality filtering
- Visibility filtering
- Diversity filtering

**Files to modify:**
- `src/core/controller.py` — Remove filtering logic
- `backend/orchestrator/orchestrator.py` — Add filtering logic

### Phase 2: Extract Ranking Logic

**Move from controller to orchestrator:**
- `_rank_apply_candidates()`
- `_job_sort_key()`
- `_select_latest_jobs()`

**Files to modify:**
- `src/core/controller.py` — Remove ranking logic
- `backend/orchestrator/orchestrator.py` — Add ranking logic

### Phase 3: Extract Application Logic

**Move from controller to workers:**
- `_apply_direct_candidate()`
- `_run_direct_apply_lane()`
- `_run_direct_apply_lanes()`

**Files to modify:**
- `src/core/controller.py` — Remove application logic
- `backend/workers/browser_worker.py` — Add application logic

### Phase 4: Extract Pipeline Orchestration

**Move from controller to orchestrator:**
- `_run_queue_cycle()`
- `_run_direct_latest_cycle()`

**Files to modify:**
- `src/core/controller.py` — Remove pipeline logic
- `backend/orchestrator/orchestrator.py` — Add pipeline logic

### Phase 5: Simplify Controller

**Keep in controller:**
- `collect_jobs()` — Job discovery
- Utility functions (move to shared utils)

**Result:**
- Controller becomes discovery-only module
- ~50 lines of focused code
- Single responsibility

---

## Execution Path After Refactoring

```
Scheduler
  ↓
scheduler.start()
  ├─ _initialize()
  └─ while running:
      ├─ _run_cycle()
      │   ├─ controller.collect_jobs()
      │   │   ├─ collect_linkedin()
      │   │   ├─ collect_indeed()
      │   │   └─ collect_naukri()
      │   └─ bridge.enqueue_jobs()
      │       ├─ Create tasks
      │       ├─ Enqueue to queue
      │       └─ Emit events
      └─ sleep(interval)

Orchestrator
  ↓
orchestrator.start()
  └─ while running:
      ├─ dequeue_task()
      ├─ filter_task()
      │   ├─ Entry level
      │   ├─ Policy
      │   ├─ AI
      │   ├─ Quality
      │   ├─ Visibility
      │   └─ Diversity
      ├─ rank_task()
      ├─ find_worker()
      ├─ execute_task()
      │   └─ worker.execute()
      └─ update_state()
```

---

## Responsibility Transfer Summary

### FROM Controller TO Orchestrator

| Responsibility | Lines | Reason |
|---|---|---|
| Entry level filtering | ~10 | Execution decision |
| Policy filtering | ~10 | Execution decision |
| AI filtering | ~80 | Execution decision |
| Quality filtering | ~30 | Execution decision |
| Visibility filtering | ~20 | Execution decision |
| Diversity filtering | ~10 | Execution decision |
| Job ranking | ~20 | Execution ordering |
| Pipeline orchestration | ~300 | Execution coordination |
| **Total** | **~480** | **~49% of controller** |

### FROM Controller TO Workers

| Responsibility | Lines | Reason |
|---|---|---|
| Direct apply | ~80 | Task execution |
| Apply lanes | ~80 | Concurrent execution |
| **Total** | **~160** | **~16% of controller** |

### KEEP in Controller

| Responsibility | Lines | Reason |
|---|---|---|
| Job discovery | ~30 | Core discovery |
| Utility functions | ~100 | Shared utilities |
| **Total** | **~130** | **~13% of controller** |

### MOVE to Scheduler

| Responsibility | Lines | Reason |
|---|---|---|
| Scheduling loop | ~30 | Already moved |
| **Total** | **~30** | **~3% of controller** |

---

## Impact Analysis

### Before Refactoring

```
controller.py: 983 lines
├─ Scheduling: 30 lines (3%)
├─ Discovery: 30 lines (3%)
├─ Filtering: 160 lines (16%)
├─ Ranking: 40 lines (4%)
├─ Application: 160 lines (16%)
├─ Orchestration: 300 lines (31%)
├─ Utilities: 100 lines (10%)
└─ Other: 193 lines (20%)
```

### After Refactoring

```
controller.py: ~130 lines
├─ Discovery: 30 lines (23%)
└─ Utilities: 100 lines (77%)

orchestrator.py: +480 lines
├─ Filtering: 160 lines
├─ Ranking: 40 lines
└─ Orchestration: 280 lines

workers/browser_worker.py: +160 lines
├─ Application: 160 lines
```

**Result:**
- Controller reduced by 87% (983 → 130 lines)
- Single responsibility (discovery only)
- Clear separation of concerns
- Easier to maintain and test

---

## Refactoring Scope

### What WILL Change

1. **controller.py** — Remove filtering, ranking, application, orchestration logic
2. **orchestrator.py** — Add filtering, ranking, orchestration logic
3. **browser_worker.py** — Add application logic

### What WILL NOT Change

- ✅ Job discovery logic
- ✅ Platform integrations
- ✅ Storage schema
- ✅ AI scoring
- ✅ Runtime infrastructure
- ✅ Scheduler
- ✅ Bridge
- ✅ Event system
- ✅ State manager
- ✅ Queue system

---

## Minimal Refactoring Approach

**Goal:** Move only execution responsibilities, keep discovery intact

**Strategy:**
1. Extract filtering functions from controller
2. Extract ranking functions from controller
3. Extract application functions from controller
4. Extract orchestration functions from controller
5. Keep discovery functions in controller
6. Keep utility functions (move to shared utils)

**Result:**
- Minimal changes to existing code
- No new architecture layers
- No new dependencies
- No learning/memory/skills systems
- Pure responsibility redistribution

---

## Summary

**Current State:**
- Controller owns 15+ responsibilities
- 983 lines of mixed concerns
- Scheduling, discovery, filtering, ranking, application, orchestration all mixed

**Target State:**
- Controller owns 1 responsibility (discovery)
- ~130 lines of focused code
- Clear separation: Scheduler → Discovery → Queue → Orchestrator → Workers

**Refactoring:**
- Move filtering to orchestrator
- Move ranking to orchestrator
- Move application to workers
- Move orchestration to orchestrator
- Keep discovery in controller
- Move utilities to shared module

**Impact:**
- Controller reduced by 87%
- Single responsibility principle
- Cleaner execution path
- Easier maintenance and testing


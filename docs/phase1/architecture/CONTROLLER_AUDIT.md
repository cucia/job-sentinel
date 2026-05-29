# Controller.py Audit - Scheduling Responsibilities

**Date:** 2026-05-29  
**Scope:** Identify scheduling responsibilities in controller.py for extraction into scheduler

---

## Current Controller Structure

### Entry Point: `main()` (lines 951-978)

**Current Responsibilities:**
1. Load settings
2. Parse command-line arguments (--platforms)
3. Parse environment variables (JOBSENTINEL_PLATFORMS)
4. **Implement scheduling loop** (while True + time.sleep)
5. Call run_cycle() at intervals

**Scheduling Logic:**
```python
while True:
    run_cycle(platforms_override or None)
    time.sleep(interval)
```

**Configuration:**
- Interval: `settings.get("app", {}).get("run_interval_seconds", 300)` (default 300s)
- Platform override: CLI args or env var

### Execution Entry: `run_cycle()` (lines 914-948)

**Current Responsibilities:**
1. Load base directory
2. Load settings
3. Load profile
4. Get platforms registry
5. Get enrichers registry
6. Resolve database path
7. Initialize database
8. Get model state
9. Determine pipeline mode
10. Delegate to appropriate pipeline (_run_direct_latest_cycle or _run_queue_cycle)

**Pipeline Selection:**
```python
pipeline_mode = settings.get("app", {}).get("pipeline_mode") or "direct_latest"
if pipeline_mode == "direct_latest":
    _run_direct_latest_cycle(...)
else:
    _run_queue_cycle(...)
```

---

## Scheduling Responsibilities to Extract

### Tier 1: Core Scheduling (MUST EXTRACT)

| Responsibility | Location | Reason |
|---|---|---|
| Interval loop | main() line 976-978 | Pure scheduling |
| Interval configuration | main() line 954 | Scheduling config |
| Platform override parsing | main() line 957-974 | Scheduling input |
| Cycle invocation | main() line 977 | Scheduling action |

### Tier 2: Initialization (SHOULD EXTRACT)

| Responsibility | Location | Reason |
|---|---|---|
| Settings loading | run_cycle() line 916 | Needed for scheduling |
| Profile loading | run_cycle() line 917 | Needed for scheduling |
| Platform registry | run_cycle() line 918 | Needed for scheduling |
| Enrichers registry | run_cycle() line 919 | Needed for scheduling |
| DB path resolution | run_cycle() line 921 | Needed for scheduling |
| DB initialization | run_cycle() line 922 | Needed for scheduling |
| Model state loading | run_cycle() line 923 | Needed for scheduling |

### Tier 3: Pipeline Selection (KEEP IN CONTROLLER)

| Responsibility | Location | Reason |
|---|---|---|
| Pipeline mode selection | run_cycle() line 925-937 | Business logic, not scheduling |
| Cycle delegation | run_cycle() line 939-948 | Business logic, not scheduling |

---

## What Stays in Controller

The controller should retain:

1. **_run_queue_cycle()** — Job discovery + filtering + queueing (lines 358-619)
2. **_run_direct_latest_cycle()** — Direct latest pipeline (lines 622-911)
3. **collect_jobs()** — Job collection from platforms (lines 326-355)
4. **Pipeline selection logic** — Choose between queue vs direct_latest

The controller becomes a **pipeline executor**, not a scheduler.

---

## Scheduler Responsibilities

The new scheduler should handle:

1. **Interval-based execution** — Run at configurable intervals
2. **Configuration management** — Load interval, platform overrides
3. **Initialization** — Setup settings, profile, registries, DB
4. **Cycle invocation** — Call controller.run_cycle()
5. **Error handling** — Catch and log errors, continue scheduling
6. **Logging** — Log scheduling events

---

## Proposed Scheduler Interface

```python
class RuntimeScheduler:
    def __init__(self, base_dir: str, interval_seconds: int = 300):
        """Initialize scheduler with configuration."""
        pass
    
    def start(self, platforms_override: list[str] = None) -> None:
        """Start scheduler loop."""
        pass
    
    def stop(self) -> None:
        """Stop scheduler gracefully."""
        pass
    
    def run_once(self, platforms_override: list[str] = None) -> None:
        """Execute single cycle (for testing)."""
        pass
```

---

## Migration Path

### Phase 1: Extract Scheduling (This Task)

1. Create `scheduler.py` with RuntimeScheduler
2. Move interval loop from main() to scheduler
3. Move initialization from run_cycle() to scheduler
4. Keep controller.run_cycle() as pipeline executor
5. Update main() to use scheduler

### Phase 2: Integration (Future)

1. Connect scheduler to runtime orchestrator
2. Replace direct cycle execution with task enqueueing
3. Let orchestrator handle execution

---

## Current Code Locations

| Component | File | Lines |
|---|---|---|
| Scheduling loop | controller.py | 976-978 |
| Interval config | controller.py | 954 |
| Platform override | controller.py | 957-974 |
| Initialization | controller.py | 915-923 |
| Pipeline selection | controller.py | 925-948 |
| Job discovery | controller.py | 358-619 |
| Direct pipeline | controller.py | 622-911 |

---

## Summary

**Scheduling Responsibilities (Extract):**
- Interval loop
- Configuration loading
- Platform override parsing
- Initialization
- Cycle invocation

**Business Logic (Keep):**
- Job discovery
- Job filtering
- Job queueing
- Pipeline selection
- Direct latest execution

**Result:**
- Scheduler: Lightweight, focused on timing and initialization
- Controller: Focused on job discovery and pipeline execution
- Clean separation of concerns


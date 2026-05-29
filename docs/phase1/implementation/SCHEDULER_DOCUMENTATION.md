# RuntimeScheduler - Integration Documentation

**Date:** 2026-05-29  
**Status:** ✅ Complete and tested  
**Tests:** 7/7 passing

---

## Overview

The `RuntimeScheduler` is a minimal, lightweight scheduler that:

1. Runs at configurable intervals
2. Triggers job discovery via existing collectors
3. Converts discovered jobs into runtime tasks
4. Enqueues tasks into the runtime queue
5. Hands control to the existing orchestrator

**Key Design:**
- No external dependencies (no Celery, Redis, APScheduler)
- Deferred imports to avoid dependency bloat
- Integrates with existing controller and runtime
- Simple, easy to reason about

---

## Architecture

```
RuntimeScheduler
    ↓
_initialize()
    ├─ Load settings
    ├─ Load profile
    ├─ Get platforms
    ├─ Initialize database
    └─ Create RuntimeBridge
    ↓
start() / run_once()
    ↓
_run_cycle()
    ├─ Collect jobs (via controller.collect_jobs)
    ├─ Enqueue jobs (via RuntimeBridge)
    └─ Log queue status
    ↓
RuntimeBridge
    ├─ Enqueue tasks into queue
    ├─ Update runtime state
    └─ Emit events
    ↓
RuntimeOrchestrator
    └─ Execute tasks
```

---

## Usage

### Basic Usage

```python
from src.core.scheduler import RuntimeScheduler

# Create scheduler
scheduler = RuntimeScheduler(base_dir="/path/to/jobsentinel", interval_seconds=300)

# Run single cycle (for testing)
scheduler.run_once()

# Start scheduler loop
scheduler.start()
```

### With Platform Override

```python
# Run only LinkedIn
scheduler.run_once(platforms_override=["linkedin"])

# Start loop with specific platforms
scheduler.start(platforms_override=["linkedin", "indeed"])
```

### Via Factory

```python
from src.core.scheduler import create_scheduler
from src.core.config import load_settings

settings = load_settings(base_dir)
scheduler = create_scheduler(base_dir, settings)
scheduler.start()
```

### Via CLI

```bash
# Run scheduler with default interval
python3 -m src.core.scheduler

# Run single cycle
python3 -m src.core.scheduler --once

# Run specific platforms
python3 -m src.core.scheduler --platforms linkedin,indeed

# Run single cycle with specific platforms
python3 -m src.core.scheduler --once --platforms linkedin
```

### Via Environment Variable

```bash
# Set platforms via env var
export JOBSENTINEL_PLATFORMS=linkedin,naukri
python3 -m src.core.scheduler
```

---

## Configuration

### Settings (configs/settings.yaml)

```yaml
app:
  run_interval_seconds: 300  # Default: 300 (5 minutes)
  use_ai: false
  apply_all: false
  pipeline_mode: direct_latest
platforms:
  enabled: [linkedin, indeed, naukri]
storage:
  db_path: data/jobsentinel.db
```

### Interval

- Default: 300 seconds (5 minutes)
- Configurable via `settings.yaml`
- Overridable via constructor

---

## API Reference

### RuntimeScheduler

```python
class RuntimeScheduler:
    def __init__(self, base_dir: str, interval_seconds: int = 300)
    def run_once(self, platforms_override: list[str] = None) -> None
    def start(self, platforms_override: list[str] = None) -> None
    def stop(self) -> None
    def get_status(self) -> dict
```

### Factory Function

```python
def create_scheduler(base_dir: str, settings: dict) -> RuntimeScheduler
```

### Status Response

```python
{
    "status": "running" | "stopped" | "not_initialized",
    "interval_seconds": 300,
    "queue_size": 42,
    "orchestrator": {
        "running": True,
        "active_tasks": 5,
        "queue_size": 42,
        "max_concurrent": 5,
        "workers": 1,
    },
    "reviews": {
        "pending": 3,
        "reviewed": 12,
        "total": 15,
    }
}
```

---

## Integration Points

### With Controller

The scheduler calls `controller.collect_jobs()` to discover jobs:

```python
from src.core.controller import collect_jobs

jobs = collect_jobs(settings, profile, enabled_override=platforms)
```

The controller remains unchanged. It still provides:
- Job discovery
- Job filtering
- Pipeline selection

### With RuntimeBridge

The scheduler uses `RuntimeBridge` to enqueue jobs:

```python
from backend.bridge import create_runtime_bridge

bridge = create_runtime_bridge(base_dir, settings, profile, platforms)
task_ids = bridge.enqueue_jobs(jobs, priority=0)
```

The bridge handles:
- Task creation
- Queue enqueueing
- State management
- Event emission

### With RuntimeOrchestrator

The orchestrator executes tasks from the queue:

```
Scheduler → Queue → Orchestrator → Workers
```

The scheduler doesn't interact directly with the orchestrator. It just enqueues tasks.

---

## Error Handling

### Graceful Degradation

If a cycle fails, the scheduler logs the error and continues:

```python
try:
    self._run_cycle(platforms_override)
except Exception as e:
    log(f"[Scheduler] Cycle error: {e}")
    # Continue to next cycle
```

### Keyboard Interrupt

Scheduler handles Ctrl+C gracefully:

```python
try:
    while self._running:
        self._run_cycle()
        time.sleep(self.interval_seconds)
except KeyboardInterrupt:
    log("[Scheduler] Interrupted")
finally:
    self.stop()
```

---

## Testing

### Unit Tests

```bash
python3 -m src.core.test_scheduler_unit
```

**Tests:**
- ✅ Scheduler creation
- ✅ Status reporting
- ✅ DB path resolution
- ✅ Factory function
- ✅ Default interval
- ✅ Error handling
- ✅ Stop method

### Integration Tests

```bash
python3 -m src.core.test_scheduler
```

**Tests:**
- Scheduler initialization
- Single cycle execution
- Job discovery and enqueueing
- Queue population
- Orchestrator integration

---

## Logging

Scheduler logs all events:

```
[Scheduler] Starting
[Scheduler] Runtime infrastructure initialized
[Scheduler] Collected 42 jobs
[Scheduler] Enqueued 35 tasks
[Scheduler] Queue size: 35
[Scheduler] Cycle error: <error>
[Scheduler] Stopped
```

---

## Responsibilities

### Scheduler Owns

- ✅ Interval-based execution
- ✅ Configuration loading
- ✅ Initialization
- ✅ Cycle invocation
- ✅ Error handling
- ✅ Logging

### Scheduler Does NOT Own

- ❌ Job discovery (delegated to controller)
- ❌ Job filtering (delegated to controller)
- ❌ Task execution (delegated to orchestrator)
- ❌ State management (delegated to runtime)
- ❌ Learning or feedback (Phase 2+)

---

## Migration from Controller

### Before (Controller-driven)

```python
# controller.py main()
while True:
    run_cycle()
    time.sleep(interval)
```

### After (Scheduler-driven)

```python
# scheduler.py main()
scheduler = create_scheduler(base_dir, settings)
scheduler.start()
```

The controller's `run_cycle()` remains unchanged. It's now called by the scheduler instead of main().

---

## Future Enhancements (Out of Scope)

- Distributed scheduling
- Task dependencies
- Conditional workflows
- Advanced retry strategies
- Scheduling optimization
- Performance tuning

These are Phase 2+ features.

---

## Summary

The `RuntimeScheduler` is a minimal, focused scheduler that:

- ✅ Runs at configurable intervals
- ✅ Triggers job discovery
- ✅ Enqueues tasks into runtime
- ✅ Hands control to orchestrator
- ✅ Has no external dependencies
- ✅ Is easy to understand and maintain
- ✅ Integrates cleanly with existing code

It completes the Phase 1 runtime backbone by providing the entry point for periodic execution.


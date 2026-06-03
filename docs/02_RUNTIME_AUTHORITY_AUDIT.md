# 02. Runtime Authority Audit

**Date:** 2026-06-03  
**Purpose:** Determine which runtime is authoritative (src/ vs backend/)

---

## Execution Authority

**ANSWER: Backend is authoritative ✅**

---

## Evidence: Job Processing Flow

### Entry Point

**File:** `backend/bridge.py`  
**Method:** `RuntimeBridge.enqueue_jobs(jobs: list)` (line 110-128)

This is where jobs from discovery enter the runtime:

```python
def enqueue_jobs(self, jobs: list, priority: int = 0) -> list:
    task_ids = []
    for job in jobs:
        try:
            task_id = self.enqueue_job(job, priority)  # LINE 124
            task_ids.append(task_id)
        except Exception as e:
            log(f"[Bridge] Failed to enqueue job: {e}")
    return task_ids
```

### Task Creation with Classification

**File:** `backend/bridge.py`  
**Method:** `RuntimeBridge.enqueue_job(job)` (line 88-106)

```python
def enqueue_job(self, job: dict, priority: int = 0) -> str:
    # Classification happens HERE
    classification = self.classifier.classify(url=job_url, page_title=job_title)  # LINE 97
    
    # Task enriched with workflow data
    task = self.orchestrator.enqueue_task(
        metadata={
            "workflow_type": classification.workflow_type.value,
            "execution_strategy": classification.execution_strategy.value,
            "workflow_confidence": classification.confidence_score,
        }
    )
```

### Execution Control

**File:** `backend/orchestrator/orchestrator.py`  
**Method:** `RuntimeOrchestrator.start()` (line 40)

```python
async def start(self) -> None:
    self._running = True
    try:
        while self._running:
            await self._process_batch()
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Orchestrator error: {e}")
        self._running = False
```

### Handler Routing

**File:** `backend/orchestrator/orchestrator.py`  
**Method:** `_route_to_workflow(task)` (line 111-134)

```python
routing_result = self.workflow_registry.route_task(task)
# Routes to appropriate handler based on workflow_type
```

---

## Evidence: src/ is NOT execution

### src/core/controller.py

**Only used for:** Utility function `_make_job_key()`

**Called by:** `backend/bridge.py` line 99

```python
from src.core.controller import _make_job_key
job_key = _make_job_key(job)
```

**Dead code in src/core/controller.py:**
- ❌ `apply_to_job()` - NOT called
- ❌ `apply_indeed()` - NOT called
- ❌ `apply_naukri()` - NOT called
- ❌ `apply_linkedin()` - NOT called
- ❌ All legacy execution logic - NOT called

**Verification:**
```bash
grep -r "from src.core.controller import apply" backend/
# Result: No matches

grep -r "apply_to_job\|apply_indeed\|apply_naukri" backend/
# Result: No matches
```

### src/core/controller_simplified.py

**Usage:** NOT imported by backend/ at all

**Verification:**
```bash
grep -r "controller_simplified" backend/
# Result: No matches
```

---

## Authoritative Runtime Call Chain

```
Job Discovery (src/platforms/*.collect_jobs())
  ↓ Returns job dict
  
Backend Entry (backend/bridge.enqueue_jobs())
  ├─ Classifier.classify()
  ├─ Create Task with workflow_type
  └─ Queue job
  ↓
Orchestrator Control (backend/orchestrator.start())
  ├─ _process_batch()
  ├─ _execute_task()
  ├─ _route_to_workflow()
  └─ Handler.prepare_for_processing()
```

---

## Conclusion

✅ **Backend IS the authoritative runtime**

Evidence:
- Backend owns job entry point
- Backend performs classification
- Backend controls execution
- Backend routes to handlers
- src/ only provides discovery data
- src/ execution code is dead (not called)


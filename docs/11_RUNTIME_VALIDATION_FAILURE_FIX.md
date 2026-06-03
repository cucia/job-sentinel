# Runtime Validation Failure Audit

**Date:** 2026-06-03T18:42:39Z  
**Issue:** Task reaches orchestrator with workflow_type = None, causing orchestrator._route_to_workflow() to fail

---

## 1. Root Cause Analysis

### Failure Chain

```
Task created by test (line 78-90)
  ├─ task_id = "task-001"
  ├─ job_id = "job-001"
  ├─ source_platform = "linkedin"
  ├─ metadata = {...job data...}
  └─ workflow_type = None  ← NOT ATTACHED
  ↓
orchestrator.enqueue_task() called
  ↓
Task queued with status = QUEUED
  ↓
orchestrator.process_single_task() called
  ↓
orchestrator._execute_task(task)
  ├─ Line 86: workflow_result = self._route_to_workflow(task)
  └─ workflow_type is None → fails
  ↓
_route_to_workflow() line 121-125:
  if not task.workflow_type:
      return {"valid": False, "reason": "No workflow_type attached to task"}
  ↓
orchestrator._execute_task() line 88-91:
  if not workflow_result.get("valid", False):
      await self._handle_execution_error(task, reason)
  ↓
_handle_execution_error() attempts:
  state_manager.transition_to_manual_review(task, reason)
  ↓
ERROR: Cannot transition from QUEUED to MANUAL_REVIEW
```

### Root Cause

**Test creates tasks WITHOUT workflow classification**

**File:** `backend/test_integration.py` line 78-90

```python
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
```

**Missing:** workflow_type is not attached to task metadata

**Why it fails:**
- Bridge.enqueue_job() normally calls classifier (line 97 in bridge.py)
- Test calls orchestrator.enqueue_task() directly (bypasses bridge)
- No classifier, no workflow_type attachment

---

## 2. Correct Task Lifecycle

### How Tasks Are SUPPOSED to Be Created

**File:** `backend/bridge.py:enqueue_job()` lines 88-106

```python
def enqueue_job(self, job: dict, priority: int = 0) -> str:
    # Step 1: Extract URL and title
    job_url = job.get("url") or job.get("link") or ""
    job_title = job.get("title") or ""
    
    # Step 2: CLASSIFY workflow
    classification = self.classifier.classify(url=job_url, page_title=job_title)  # LINE 97
    
    # Step 3: Create task WITH workflow data
    task = self.orchestrator.enqueue_task(
        metadata={
            "job": job,
            "workflow_type": classification.workflow_type.value,              # ATTACHED
            "workflow_confidence": classification.confidence_score,           # ATTACHED
            "execution_strategy": classification.execution_strategy.value,    # ATTACHED
            "workflow_indicators": classification.indicators,                 # ATTACHED
        },
    )
```

**Orchestrator.enqueue_task() then stores what's passed in metadata:**

```python
def enqueue_task(self, ..., metadata=None):
    task = Task(...)
    task.metadata = metadata  # Gets classifier results
```

### How Test Currently Creates Tasks

**File:** `backend/test_integration.py` lines 78-90

```python
task = orchestrator.enqueue_task(
    task_id="task-001",
    ...
    metadata={
        "job": {...}  # Only job data, NO workflow info
    },
)
```

**Result:** Task has no workflow_type

---

## 3. State Machine Analysis

### Valid Task Lifecycle

**File:** `backend/state/state_manager.py`

```
DISCOVERED ──enqueue──> QUEUE
                          ↓
                        RUNNING (transition_to_running)
                          ↓
                    ┌─────┴─────┐
                    ↓           ↓
                COMPLETED   FAILED
                    
MANUAL_REVIEW (only from RUNNING, not from QUEUE)
```

### Current Error

```
QUEUE → Orchestrator tries to execute
        → _route_to_workflow fails (no workflow_type)
        → _handle_execution_error() called
        → Attempts: transition_to_manual_review() from QUEUE
        → ERROR: Invalid transition QUEUE → MANUAL_REVIEW
```

### The Problem

State manager correctly rejects invalid transition. But orchestrator error handler assumes task is already RUNNING.

**File:** `backend/orchestrator/orchestrator.py` lines 88-91

```python
if not workflow_result.get("valid", False):
    log(f"[Orchestrator] Task {task.task_id} workflow routing failed: {workflow_result.get('reason')}")
    await self._handle_execution_error(task, workflow_result.get("reason", "Unknown error"))
    return
```

**_handle_execution_error() (line 153+) attempts:**

```python
async def _handle_execution_error(self, task: Task, error_message: str):
    ...
    await self.state_manager.transition_to_manual_review(task, error_message)
```

**But task is still QUEUE, not RUNNING.**

---

## 4. Root Cause Summary

| Issue | Component | Problem |
|---|---|---|
| **Missing Data** | Test | Creates tasks without workflow_type (bypasses classification) |
| **Validation Failure** | Orchestrator | _route_to_workflow() correctly rejects task without workflow_type |
| **Invalid State Transition** | Error Handler | Tries to transition QUEUE → MANUAL_REVIEW (invalid) |
| **Assumption Error** | Orchestrator | Error handler assumes task is RUNNING, but it's QUEUE |

---

## 5. Valid Transitions from QUEUE

**From state_manager.py:**

```
QUEUE can only transition to:
- RUNNING (transition_to_running)
- FAILED (directly mark failed)
- COMPLETED (directly mark completed)

Cannot transition to:
- MANUAL_REVIEW (invalid - only from RUNNING)
- DISCOVERED (invalid - already discovered)
```

**Conclusion:** Orchestrator error handler is wrong. It should not try to transition QUEUE → MANUAL_REVIEW.

---

## 6. The Two Problems to Fix

### Problem 1: Test Creates Tasks Incorrectly

**File:** `backend/test_integration.py` line 78

**Current:**
```python
task = orchestrator.enqueue_task(
    metadata={"job": {...}}  # Missing workflow_type
)
```

**Should Be:**
```python
task = orchestrator.enqueue_task(
    metadata={
        "job": {...},
        "workflow_type": "linkedin_easy_apply",  # Add classification
        "execution_strategy": "linkedin_easy_apply_flow",
        "workflow_confidence": 0.95,
    }
)
```

### Problem 2: Orchestrator Error Handler Invalid Transition

**File:** `backend/orchestrator/orchestrator.py` line 153+

**Current:**
```python
async def _handle_execution_error(self, task: Task, error_message: str):
    await self.state_manager.transition_to_manual_review(task, error_message)
```

**Issue:** Tries invalid QUEUE → MANUAL_REVIEW transition

**Should Be:**
```python
async def _handle_execution_error(self, task: Task, error_message: str):
    # Task is QUEUE, cannot transition to MANUAL_REVIEW
    # Must transition to FAILED instead
    await self.state_manager.transition_to_failed(task, error_message)
```

---

## 7. Minimal Fix

### Fix 1: Update Test to Include Classification Data

**File:** `backend/test_integration.py` line 78-90

```python
# Before
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

# After
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
        },
        "workflow_type": "linkedin_easy_apply",
        "execution_strategy": "linkedin_easy_apply_flow",
        "workflow_confidence": 0.95,
    },
)
```

### Fix 2: Correct Orchestrator Error Handler

**File:** `backend/orchestrator/orchestrator.py` 

Find `_handle_execution_error()` method and replace:

```python
async def _handle_execution_error(self, task: Task, error_message: str):
    """Handle task execution error."""
    # Task may be in QUEUE or RUNNING status
    # Only RUNNING tasks can transition to MANUAL_REVIEW
    # QUEUE tasks should transition to FAILED
    
    if task.status == TaskStatus.QUEUE:
        # Task never reached running state - mark as failed
        await self.state_manager.transition_to_failed(task, error_message)
    elif task.status == TaskStatus.RUNNING:
        # Task was running - send to manual review
        await self.state_manager.transition_to_manual_review(task, error_message)
    else:
        # Unexpected state - log and fail
        log(f"[Orchestrator] Unexpected task status for error: {task.status}")
        await self.state_manager.transition_to_failed(task, error_message)
```

---

## 8. Evidence

### Test Creates Tasks Without Classification

**File:** `backend/test_integration.py` line 78-90

```python
task = orchestrator.enqueue_task(
    ...
    metadata={
        "job": {
            "title": "Software Engineer",
            "company": "TechCorp",
            "job_url": "https://linkedin.com/jobs/123",
        }
    },  # ← No workflow_type, execution_strategy, etc.
)
```

**Compare to Bridge:**

**File:** `backend/bridge.py` line 100-106

```python
task = self.orchestrator.enqueue_task(
    metadata={
        "job": job,
        "workflow_type": classification.workflow_type.value,         # ← PRESENT
        "workflow_confidence": classification.confidence_score,      # ← PRESENT
        "execution_strategy": classification.execution_strategy.value, # ← PRESENT
        "workflow_indicators": classification.indicators,             # ← PRESENT
    },
)
```

### Orchestrator Requires workflow_type

**File:** `backend/orchestrator/orchestrator.py` line 121-125

```python
def _route_to_workflow(self, task: Task) -> dict:
    if not task.workflow_type:
        return {
            "valid": False,
            "reason": "No workflow_type attached to task",
        }
```

### Error Handler Invalid Transition

**File:** `backend/orchestrator/orchestrator.py` line 153+

```python
async def _handle_execution_error(self, task: Task, error_message: str):
    await self.state_manager.transition_to_manual_review(task, error_message)
    # ↑ Assumes task.status == RUNNING
    # ✗ But if _route_to_workflow failed, task.status == QUEUE
```

---

## 9. Summary

| Issue | Root Cause | Fix |
|---|---|---|
| Task has no workflow_type | Test bypasses bridge/classifier | Add workflow fields to test task metadata |
| _route_to_workflow fails | workflow_type is None | Fix 1 resolves this |
| Invalid state transition | Error handler assumes RUNNING | Add status check, use FAILED for QUEUE |

---

## 10. Validation After Fix

### Test should:
1. Create task with workflow_type (Fix 1)
2. Orchestrator routes successfully (no longer fails)
3. Task executes normally
4. All tests pass

### If error occurs again:
1. Error handler checks task.status (Fix 2)
2. QUEUE → FAILED (valid transition)
3. Task marked failed with error message
4. No invalid state transition error

---

## Conclusion

**Minimal Fix Required:**

1. **Test update:** Add workflow_type and related fields to task metadata
2. **Orchestrator update:** Fix error handler to handle QUEUE status correctly

**No architectural changes needed.**  
**No refactoring required.**  
**Pure bug fixes.**


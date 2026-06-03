# 03. Call Chain Audit

**Date:** 2026-06-03  
**Purpose:** Trace exact call paths through runtime

---

## Call Chain 1: Job to Classification

**Entry:** `backend/bridge.py:enqueue_job(job)`  
**Line:** 88-106

```
enqueue_job(job)
  ├─ Line 97: classifier.classify(url, title)
  │   └─ File: backend/workflow_classification.py
  │   └─ Class: WorkflowClassifier
  │   └─ Method: classify()
  │   └─ Returns: WorkflowClassification
  │
  └─ Line 100-106: Create task with classification data
      ├─ workflow_type: classification.workflow_type.value
      ├─ execution_strategy: classification.execution_strategy.value
      ├─ workflow_confidence: classification.confidence_score
      └─ workflow_indicators: classification.indicators
```

---

## Call Chain 2: Task to Orchestrator

**Entry:** `backend/orchestrator/orchestrator.py:_process_batch()`  
**Line:** 55-69

```
start()
  └─ Event loop (line 40-49)
      └─ _process_batch() (line 55)
          ├─ Check available slots
          ├─ queue.dequeue(limit) (line 63)
          │   └─ Returns: List[Task] with workflow_type attached
          └─ Execute tasks (line 68)
              └─ _execute_task(task) (line 71)
```

---

## Call Chain 3: Orchestrator to Handlers

**Entry:** `backend/orchestrator/orchestrator.py:_execute_task(task)`  
**Line:** 75-109

```
_execute_task(task)
  ├─ Line 86: _route_to_workflow(task)
  │   ├─ Line 127: self.workflow_registry.route_task(task)
  │   │   ├─ Line 514: get_handler(task.workflow_type)
  │   │   │   └─ Returns: Handler instance (LinkedIn, Indeed, Naukri, etc.)
  │   │   └─ Line 523: handler.prepare_for_processing(task)
  │   │       └─ Returns: dict with routing result
  │   └─ Returns: routing_result
  │
  ├─ Line 98: state_manager.transition_to_running()
  ├─ Line 102: result = TaskResult.APPLIED
  └─ Line 103: _handle_result(task, result)
```

---

## Call Chain 4: Handler to Session

**Entry:** `backend/workflow/handlers.py:LinkedInEasyApplyHandler.prepare_for_processing()`  
**Line:** 162-188

```
prepare_for_processing(task)
  ├─ Line 164: validate_workflow_assignment(task)
  ├─ Line 178: create_application_session(task, url)
  │   └─ File: backend/workflow/handlers.py:WorkflowHandler
  │   └─ Line 73-86: Creates ApplicationSession
  │       ├─ Line 83: session = ApplicationSession(...)
  │       └─ Returns: ApplicationSession instance
  └─ Line 180-188: Return dict with session
      └─ "session": session
      └─ "next_step": "analyze_linkedin_page"
```

---

## Call Chain 5: Session Creation (ACTUAL)

**File:** `backend/workflow/handlers.py`  
**Method:** `WorkflowHandler.create_application_session()`  
**Line:** 73-86

```
create_application_session(task, current_url)
  ├─ Line 83: session = ApplicationSession(
  │   ├─ session_id=uuid
  │   ├─ job_id=task.job_id
  │   ├─ task_id=task.task_id
  │   ├─ workflow_type=self.workflow_type
  │   └─ current_url=current_url
  │   )
  ├─ Line 85: log session created
  └─ Line 86: Return session
```

---

## Call Chain 6: Session Analysis (NOT CALLED)

**ANALYSIS PATH:** analyze_page_and_plan()  
**File:** `backend/workflow/handlers.py`  
**Line:** 91-125

```
analyze_page_and_plan(session, page_data)  ← NOT CALLED IN RUNTIME
  ├─ Line 98: analysis = self.page_analyzer.analyze_page(page_data)
  ├─ Line 99: session.record_page_analysis(analysis)
  ├─ Line 102-106: planner = create_execution_planner()
  ├─ Line 107-110: plan = planner.generate_plan()
  └─ Line 111: session.set_execution_plan(plan)
```

**Status:** Method exists but is NEVER CALLED at runtime

---

## Active vs Inactive Paths Summary

| Call Chain | Status | Evidence |
|---|---|---|
| Job → Classification | ✅ ACTIVE | bridge.py:97 calls classifier |
| Classification → Task | ✅ ACTIVE | bridge.py:100-106 attaches data |
| Task → Orchestrator | ✅ ACTIVE | orchestrator.start() runs loop |
| Orchestrator → Handlers | ✅ ACTIVE | orchestrator.py:86 routes task |
| Handlers → Sessions | ✅ ACTIVE | handlers.py:178 creates session |
| Sessions → Analysis | ❌ INACTIVE | analyze_page_and_plan() not called |
| Analysis → Planning | ❌ INACTIVE | generate_plan() not called |

---

## Conclusion

**Active Runtime Call Chain:**
```
Job → Classification → Task → Orchestrator → Handler → Session (Creation Only)
```

**Inactive Paths (Phase 3):**
```
Session → Page Analysis → Execution Planning
```


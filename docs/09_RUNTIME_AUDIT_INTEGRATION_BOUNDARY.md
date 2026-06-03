# Runtime Audit: Application Session Integration Boundary

**Date:** 2026-06-03T18:25:53Z  
**Purpose:** Document current and future runtime states after integration boundary implementation

---

## Current Runtime State (Before page_data source)

### Component Status Matrix

| Component | Status | Called? | Evidence |
|---|---|---|---|
| **create_application_session()** | IMPLEMENTED ✅ | YES ✅ | handlers.py:178 calls it |
| **analyze_page_and_plan()** | IMPLEMENTED ✅ | NO ❌ | Never called (no page_data) |
| **page_analyzer.analyze_page()** | IMPLEMENTED ✅ | NO ❌ | Only in tests |
| **planner.generate_plan()** | IMPLEMENTED ✅ | NO ❌ | Only in tests |
| **session.record_page_analysis()** | IMPLEMENTED ✅ | NO ❌ | Not called |
| **session.set_execution_plan()** | IMPLEMENTED ✅ | NO ❌ | Not called |

### Call Chain (Current)

```
Task._execute_task()
  ├─ _route_to_workflow(task)
  │   └─ registry.route_task(task)
  │       └─ handler.prepare_for_processing(task)
  │           ├─ ✅ create_application_session(task, url)
  │           │   └─ Returns: ApplicationSession
  │           └─ ✅ Return result with session
  │
  └─ _handle_result(task, result)
```

**Execution stops after session creation.**

### Handler Return Value (Current)

```python
{
    "valid": True,
    "workflow": "linkedin_easy_apply",
    "execution_strategy": "linkedin_easy_apply_flow",
    "confidence": 0.95,
    "session": <ApplicationSession>,      # ✅ Present
    "page_analysis": None,                 # ❌ Absent
    "execution_plan": None,                # ❌ Absent
    "ready_for_execution": False,          # Analysis not done
    "reason": "AWAITING_PAGE_DATA"         # Missing page structure
}
```

**Session exists but is not populated with analysis or plan.**

---

## Integration Boundary Implementation

### What Changes

**File:** `backend/workflow/handlers.py`

**In WorkflowHandler base class:**

Add method to detect page_data:

```python
def prepare_for_processing(self, task: Task) -> dict:
    """Prepare task, with optional page_data detection."""
    
    # Step 1: Validate
    is_valid, reason = self.validate_workflow_assignment(task)
    if not is_valid:
        return {"valid": False, "reason": reason}
    
    # Step 2: Create session (ALWAYS)
    session = self.create_application_session(task, ...)
    
    # Step 3: Check for page_data (NEW)
    page_data = task.metadata.get("page_data")
    
    # Step 4: Route based on page_data presence (NEW)
    if page_data:
        return self._execute_analysis_pipeline(session, page_data, task)
    else:
        return {
            "valid": True,
            "session": session,
            "ready_for_execution": False,
            "status": "AWAITING_PAGE_DATA",
        }
```

### What Does NOT Change

- ❌ Orchestrator
- ❌ Classification
- ❌ Task model
- ❌ Queue
- ❌ State manager
- ❌ Any execution logic

### Handler Implementations

All specific handlers (LinkedIn, Indeed, Naukri, etc.) delegate to base:

```python
class LinkedInEasyApplyHandler(WorkflowHandler):
    def prepare_for_processing(self, task: Task) -> dict:
        return super().prepare_for_processing(task)
```

---

## Future Runtime State (With page_data source)

### After Browser Component is Added

**Phase 4+:** Browser automation component

```python
# Pseudo-code for future browser component
async def load_and_extract_page(job_url):
    page = await browser.goto(job_url)
    page_data = extract_page_structure(page)  # Returns dict
    return page_data

# In scheduler or entrypoint:
page_data = await load_and_extract_page(job["url"])
task.metadata["page_data"] = page_data
```

### Call Chain (Future)

```
Task._execute_task()
  ├─ _route_to_workflow(task)
  │   └─ registry.route_task(task)
  │       └─ handler.prepare_for_processing(task)
  │           ├─ ✅ create_application_session(task, url)
  │           │   └─ Returns: ApplicationSession
  │           ├─ ✅ Detect page_data in task.metadata
  │           ├─ ✅ _execute_analysis_pipeline(session, page_data, task)
  │           │   ├─ ✅ analyze_page_and_plan(session, page_data)
  │           │   │   ├─ ✅ PageAnalyzer.analyze_page(page_data)
  │           │   │   │   └─ Returns: PageAnalysisResult
  │           │   │   ├─ ✅ session.record_page_analysis(analysis)
  │           │   │   ├─ ✅ ExecutionPlanner.generate_plan(analysis)
  │           │   │   │   └─ Returns: ExecutionPlan
  │           │   │   ├─ ✅ session.set_execution_plan(plan)
  │           │   │   └─ Returns: {"session": updated, "page_analysis": ..., "execution_plan": ...}
  │           │   └─ Returns: enriched result
  │           └─ ✅ Return result with all components
  │
  └─ _handle_result(task, result)
```

### Handler Return Value (Future)

```python
{
    "valid": True,
    "workflow": "indeed",
    "execution_strategy": "generic_form_flow",
    "confidence": 0.85,
    "session": <ApplicationSession>,           # ✅ Present and updated
    "page_analysis": <PageAnalysisResult>,     # ✅ Present
    "execution_plan": <ExecutionPlan>,         # ✅ Present
    "ready_for_execution": True,               # Ready for Phase 5
    "status": "ANALYSIS_COMPLETE",
    "handler": "IndeedHandler",
}
```

**Session populated with analysis results and execution plan.**

---

## Component Status After Implementation

### Before Integration Boundary (Current)

| Component | Implemented | Connected | Executed | Status |
|---|---|---|---|---|
| create_application_session() | ✅ | ✅ | ✅ | ACTIVE |
| analyze_page_and_plan() | ✅ | ❌ | ❌ | READY |
| page_analyzer.analyze_page() | ✅ | ❌ | ❌ | READY |
| planner.generate_plan() | ✅ | ❌ | ❌ | READY |
| session.record_page_analysis() | ✅ | ❌ | ❌ | READY |
| session.set_execution_plan() | ✅ | ❌ | ❌ | READY |

### After Integration Boundary (With page_data)

| Component | Implemented | Connected | Executed | Status |
|---|---|---|---|---|
| create_application_session() | ✅ | ✅ | ✅ | ACTIVE |
| analyze_page_and_plan() | ✅ | ✅ | ✅ | ACTIVE |
| page_analyzer.analyze_page() | ✅ | ✅ | ✅ | ACTIVE |
| planner.generate_plan() | ✅ | ✅ | ✅ | ACTIVE |
| session.record_page_analysis() | ✅ | ✅ | ✅ | ACTIVE |
| session.set_execution_plan() | ✅ | ✅ | ✅ | ACTIVE |

---

## Data Flow Transformation

### Current (No page_data)

```
Input Task:
{
    "task_id": "task_001",
    "job_id": "job_001",
    "workflow_type": "linkedin_easy_apply",
    "metadata": {"job": {...}}  ← No page_data
}

Handler Processing:
  Session created (not populated)

Output:
{
    "session": <empty ApplicationSession>,
    "ready_for_execution": False,
    "status": "AWAITING_PAGE_DATA"
}
```

### Future (With page_data)

```
Input Task:
{
    "task_id": "task_001",
    "job_id": "job_001",
    "workflow_type": "linkedin_easy_apply",
    "metadata": {
        "job": {...},
        "page_data": {                    ← NEW: Page structure
            "url": "...",
            "forms": [...],
            "buttons": [...]
        }
    }
}

Handler Processing:
  Session created
  Page analyzed
  Execution plan generated
  Session populated

Output:
{
    "session": <populated ApplicationSession>,
    "page_analysis": <PageAnalysisResult>,
    "execution_plan": <ExecutionPlan>,
    "ready_for_execution": True,
    "status": "ANALYSIS_COMPLETE"
}
```

---

## Runtime Milestones

### Phase 2 (Current) ✅
- ✅ Workflow classification
- ✅ Task creation
- ✅ Orchestrator routing
- ✅ Handler creation
- ✅ Session creation

### Phase 3 (Proposed Implementation)
- ❌ Integration boundary definition
- ❌ page_data detection in handlers
- ❌ Optional analysis pipeline activation

**Current Status:** PROPOSED - No code changes yet

### Phase 4 (Future)
- ❌ Browser automation
- ❌ Page loading and extraction
- ❌ page_data injection
- ❌ Activate analysis pipeline

### Phase 5 (Future)
- ❌ Execution engine
- ❌ Task execution
- ❌ Form filling
- ❌ Application submission

---

## Risk Assessment

### Implementation Risk (Phase 3): NONE ✅

Proposed changes:
- Add page_data detection (new code path)
- Call existing analyze_page_and_plan() (already exists)
- Return AWAITING_PAGE_DATA when not available (new status)

**Risk Level:** None
- No existing code modified
- No execution logic changed
- No mocks or fakes introduced
- Pure additive

### Backward Compatibility: PRESERVED ✅

- Tasks without page_data continue to work
- Return AWAITING_PAGE_DATA (clear status)
- Session still created (existing behavior)
- No breaking changes

### Future Integration Risk (Phase 4+): LOW ✅

When page_data source is added:
- Inject into task.metadata (simple dict)
- Handler detects it (simple check)
- Call existing pipeline (already tested)
- Return enriched result (expected format)

---

## Conclusion: Integration Boundary Ready

### Current State
- ✅ All components implemented and tested
- ✅ No page_data source yet (expected)
- ✅ Handlers stop after session creation (correct behavior)

### After Integration Boundary Implementation
- ✅ Handlers can detect page_data
- ✅ Handlers activate analysis when available
- ✅ Handlers return AWAITING_PAGE_DATA when not available
- ✅ No changes to orchestrator, classification, or execution

### Path Forward
1. **Phase 3 (Proposed):** Implement integration boundary in handlers
2. **Phase 4 (Future):** Add browser component to produce page_data
3. **Phase 5 (Future):** Implement execution engine to use plans

### Status: READY FOR IMPLEMENTATION ✅

Integration boundary is well-defined, low-risk, and enables future page analysis pipeline activation without requiring any browser automation or execution logic now.


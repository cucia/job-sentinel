# Handler Integration Implementation Guide

**Date:** 2026-06-03T18:25:26Z  
**Purpose:** Implement page_data detection and optional analysis pipeline in handlers

---

## Implementation Pattern for All Handlers

### Base Handler Modification

**File:** `backend/workflow/handlers.py`  
**Class:** `WorkflowHandler` (base class)

Add method to handle page data detection:

```python
def prepare_for_processing(self, task: Task) -> dict:
    """
    Prepare task for processing.
    
    If page_data is available in task.metadata, execute analysis pipeline.
    If page_data is absent, return waiting status with clear indicator.
    """
    is_valid, reason = self.validate_workflow_assignment(task)
    if not is_valid:
        return {
            "valid": False,
            "reason": reason,
            "workflow": self.workflow_type,
        }
    
    # Create session (always)
    session = self.create_application_session(
        task,
        task.metadata.get("job", {}).get("url", "")
    )
    
    # Check for page_data in task metadata
    page_data = task.metadata.get("page_data")
    
    if page_data:
        # Page data exists - execute analysis pipeline
        log(f"[{self.__class__.__name__}] Page data available, executing analysis")
        return self._execute_analysis_pipeline(session, page_data, task)
    else:
        # Page data not available - return waiting status
        log(f"[{self.__class__.__name__}] Awaiting page data for analysis")
        return {
            "valid": True,
            "workflow": self.workflow_type,
            "execution_strategy": task.execution_strategy,
            "confidence": task.workflow_confidence,
            "session": session,
            "ready_for_execution": False,
            "status": "AWAITING_PAGE_DATA",
            "reason": "Page structure required for analysis",
            "next_step": "load_page_and_extract_structure",
            "page_url": task.metadata.get("job", {}).get("url"),
            "handler": self.__class__.__name__,
        }

def _execute_analysis_pipeline(self, session: ApplicationSession, page_data: dict, task: Task) -> dict:
    """
    Execute analysis pipeline when page_data is available.
    
    Calls existing analyze_page_and_plan() to:
    - Analyze page structure
    - Generate execution plan
    - Store in session
    """
    result = self.analyze_page_and_plan(session, page_data)
    
    return {
        "valid": True,
        "workflow": self.workflow_type,
        "execution_strategy": task.execution_strategy,
        "confidence": task.workflow_confidence,
        "session": result["session"],
        "page_analysis": result["page_analysis"],
        "execution_plan": result["execution_plan"],
        "ready_for_execution": result["ready_for_execution"],
        "status": "ANALYSIS_COMPLETE",
        "handler": self.__class__.__name__,
    }
```

---

## Specific Handler Updates

### LinkedInEasyApplyHandler

**File:** `backend/workflow/handlers.py`  
**Line:** 151

Replace current `prepare_for_processing()` with base implementation:

```python
class LinkedInEasyApplyHandler(WorkflowHandler):
    """Handler for LinkedIn Easy Apply workflow."""

    def __init__(self):
        """Initialize LinkedIn Easy Apply handler."""
        super().__init__("linkedin_easy_apply")

    def can_handle(self, task: Task) -> bool:
        """Check if task is LinkedIn Easy Apply."""
        return task.workflow_type == "linkedin_easy_apply"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare LinkedIn task for processing."""
        # Use base implementation which handles page_data detection
        return super().prepare_for_processing(task)
```

**Result:**
- ✅ If page_data exists: Analyzes and plans
- ✅ If page_data absent: Returns AWAITING_PAGE_DATA

---

### IndeedHandler

**File:** `backend/workflow/handlers.py`  
**Line:** 191

Replace current `prepare_for_processing()` with base implementation:

```python
class IndeedHandler(WorkflowHandler):
    """Handler for Indeed workflow."""

    def __init__(self):
        """Initialize Indeed handler."""
        super().__init__("indeed")

    def can_handle(self, task: Task) -> bool:
        """Check if task is Indeed."""
        return task.workflow_type == "indeed"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare Indeed task for processing."""
        # Use base implementation which handles page_data detection
        return super().prepare_for_processing(task)
```

**Result:**
- ✅ If page_data exists: Analyzes and plans
- ✅ If page_data absent: Returns AWAITING_PAGE_DATA

---

### NaukriHandler

**File:** `backend/workflow/handlers.py`  
**Line:** 231

Replace current `prepare_for_processing()` with base implementation:

```python
class NaukriHandler(WorkflowHandler):
    """Handler for Naukri workflow."""

    def __init__(self):
        """Initialize Naukri handler."""
        super().__init__("naukri")

    def can_handle(self, task: Task) -> bool:
        """Check if task is Naukri."""
        return task.workflow_type == "naukri"

    def prepare_for_processing(self, task: Task) -> dict:
        """Prepare Naukri task for processing."""
        # Use base implementation which handles page_data detection
        return super().prepare_for_processing(task)
```

**Result:**
- ✅ If page_data exists: Analyzes and plans
- ✅ If page_data absent: Returns AWAITING_PAGE_DATA

---

## Runtime Behavior After Implementation

### Scenario 1: Task WITHOUT page_data (Current State)

```python
task = Task(task_id="...", job_id="...", workflow_type="linkedin_easy_apply", ...)
task.metadata = {"job": {...}}  # No page_data

handler = LinkedInEasyApplyHandler()
result = handler.prepare_for_processing(task)

# Result:
{
    "valid": True,
    "workflow": "linkedin_easy_apply",
    "session": <ApplicationSession>,
    "ready_for_execution": False,
    "status": "AWAITING_PAGE_DATA",
    "reason": "Page structure required for analysis",
    "next_step": "load_page_and_extract_structure",
    "page_url": "https://www.linkedin.com/jobs/view/123",
}
```

**Handler:** Creates session, returns AWAITING_PAGE_DATA status  
**Next Step:** Browser component must load page and provide page_data

---

### Scenario 2: Task WITH page_data (Future State)

```python
task = Task(task_id="...", job_id="...", workflow_type="indeed", ...)
task.metadata = {
    "job": {...},
    "page_data": {
        "url": "https://indeed.com/viewjob?jk=123",
        "forms": [...],
        "buttons": [...],
    }
}

handler = IndeedHandler()
result = handler.prepare_for_processing(task)

# Result:
{
    "valid": True,
    "workflow": "indeed",
    "session": <ApplicationSession>,
    "page_analysis": <PageAnalysisResult>,
    "execution_plan": <ExecutionPlan>,
    "ready_for_execution": True,
    "status": "ANALYSIS_COMPLETE",
    "handler": "IndeedHandler",
}
```

**Handler:** Creates session, analyzes page, generates plan, returns enriched result  
**Next Step:** Execution engine processes plan

---

## Call Chain After Implementation

### With page_data Present

```
Task._execute_task()
  ↓
Orchestrator._route_to_workflow(task)
  ↓
WorkflowHandlerRegistry.route_task(task)
  ↓
LinkedInEasyApplyHandler.prepare_for_processing(task)
  ├─ create_application_session(task, url)
  │   └─ Returns: ApplicationSession
  ├─ task.metadata.get("page_data") → page_data exists
  ├─ _execute_analysis_pipeline(session, page_data, task)
  │   ├─ analyze_page_and_plan(session, page_data)
  │   │   ├─ PageAnalyzer.analyze_page(page_data)
  │   │   │   └─ Returns: PageAnalysisResult
  │   │   ├─ session.record_page_analysis(analysis)
  │   │   ├─ ExecutionPlanner.generate_plan(analysis)
  │   │   │   └─ Returns: ExecutionPlan
  │   │   ├─ session.set_execution_plan(plan)
  │   │   └─ Returns: {"session": updated, "page_analysis": ..., "execution_plan": ...}
  │   └─ Returns: enriched dict
  └─ Returns: result with session, analysis, plan
```

### Without page_data (Current)

```
Task._execute_task()
  ↓
Orchestrator._route_to_workflow(task)
  ↓
WorkflowHandlerRegistry.route_task(task)
  ↓
LinkedInEasyApplyHandler.prepare_for_processing(task)
  ├─ create_application_session(task, url)
  │   └─ Returns: ApplicationSession
  ├─ task.metadata.get("page_data") → None
  └─ Returns: {"session": ..., "status": "AWAITING_PAGE_DATA"}
```

---

## Contract Enforcement

### Validation in prepare_for_processing()

Current implementation will:

1. ✅ Always create and return a session
2. ✅ Check for page_data presence
3. ✅ If page_data present: Call analyze_page_and_plan()
4. ✅ If page_data absent: Return clear AWAITING_PAGE_DATA status
5. ✅ Never fabricate page data
6. ✅ Never simulate analysis
7. ✅ Never create fake execution plans

### Error Handling

If analyze_page_and_plan() fails (page_data malformed):

```python
try:
    result = self.analyze_page_and_plan(session, page_data)
    return {...success result...}
except Exception as e:
    log(f"[{self.__class__.__name__}] Analysis failed: {e}")
    return {
        "valid": False,
        "reason": f"Page analysis failed: {str(e)}",
        "session": session,
        "page_data_error": True,
    }
```

---

## Testing the Integration Boundary

### Test 1: Handler without page_data

```python
def test_handler_awaiting_page_data():
    task = Task(task_id="test_1", job_id="job_1", workflow_type="linkedin_easy_apply")
    task.metadata = {"job": {"url": "https://www.linkedin.com/jobs/view/123"}}
    
    handler = LinkedInEasyApplyHandler()
    result = handler.prepare_for_processing(task)
    
    assert result["valid"] == True
    assert result["ready_for_execution"] == False
    assert result["status"] == "AWAITING_PAGE_DATA"
    assert result["session"] is not None
```

### Test 2: Handler with page_data (validates contract)

```python
def test_handler_with_page_data():
    task = Task(task_id="test_2", job_id="job_2", workflow_type="indeed")
    
    # Page data structure (from PageAnalyzer schema)
    page_data = {
        "url": "https://indeed.com/viewjob?jk=123",
        "title": "Apply Now - Indeed",
        "forms": [{
            "id": "form_1",
            "name": "application",
            "elements": [
                {"id": "email", "type": "input", "required": True, "visible": True}
            ]
        }],
        "buttons": [{"id": "apply", "text": "Apply Now"}],
        "has_submit_button": True,
    }
    
    task.metadata = {"job": {"url": "..."}, "page_data": page_data}
    
    handler = IndeedHandler()
    result = handler.prepare_for_processing(task)
    
    assert result["valid"] == True
    assert result["ready_for_execution"] == True
    assert result["status"] == "ANALYSIS_COMPLETE"
    assert result["session"] is not None
    assert result["page_analysis"] is not None
    assert result["execution_plan"] is not None
```

---

## Backward Compatibility

### Existing Code

Current code that creates tasks without page_data continues to work:

```python
# Existing code:
bridge.enqueue_job(job)  # No page_data in metadata

# Handler receives task without page_data
# Returns: {"session": ..., "status": "AWAITING_PAGE_DATA"}

# ✅ Continues to work - graceful degradation
```

### Future Code

When browser component is added:

```python
# Future code:
page_data = browser.extract_page_structure(url)
task.metadata["page_data"] = page_data
bridge.enqueue_job(job)  # With page_data

# Handler receives task with page_data
# Executes analysis pipeline
# Returns: {"session": ..., "page_analysis": ..., "execution_plan": ...}

# ✅ New functionality activates automatically
```

---

## Summary

### Implementation: Integration boundary in handlers

- ✅ Detect page_data presence
- ✅ Call analyze_page_and_plan() when available
- ✅ Return AWAITING_PAGE_DATA when not available
- ✅ No mock data
- ✅ No fabricated results
- ✅ Clean contract enforcement

### Next Phase (Phase 4+): Browser component

- Add page loading and extraction
- Populate page_data
- Inject into task.metadata
- Handlers activate analysis automatically

### Ready Now

- ✅ All handlers can detect page_data
- ✅ All components exist and tested
- ✅ Integration boundary defined
- ✅ Call chain ready to activate


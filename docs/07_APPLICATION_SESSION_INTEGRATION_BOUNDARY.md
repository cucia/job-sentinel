# Application Session Integration Boundary

**Date:** 2026-06-03T18:24:53Z  
**Purpose:** Define integration boundary for page data and analysis pipeline

---

## 1. Current Runtime State

### What Handlers Receive

**File:** `backend/orchestrator/orchestrator.py`  
**Method:** `_execute_task(task: Task)` line 75

```python
workflow_result = self._route_to_workflow(task)
```

**Task contents:**
- ✅ task_id
- ✅ job_id
- ✅ task.workflow_type (e.g., "linkedin_easy_apply")
- ✅ task.execution_strategy
- ✅ task.workflow_confidence
- ✅ task.metadata (contains original job dict)

**What is NOT present:**
- ❌ page_data
- ❌ DOM or HTML
- ❌ Page structure information
- ❌ Form field data

### Current Handler Flow

**File:** `backend/workflow/handlers.py`  
**Method:** `LinkedInEasyApplyHandler.prepare_for_processing()` line 162

```python
def prepare_for_processing(self, task: Task) -> dict:
    # Step 1: Validate assignment
    is_valid, reason = self.validate_workflow_assignment(task)
    if not is_valid:
        return {"valid": False, "reason": reason}
    
    # Step 2: Create session
    session = self.create_application_session(
        task,
        task.metadata.get("job", {}).get("url", "")
    )
    
    # Step 3: Return (STOPS HERE - no page analysis)
    return {
        "valid": True,
        "workflow": self.workflow_type,
        "session": session,
        "next_step": "analyze_linkedin_page",
    }
```

**Current Return Value:**
```python
{
    "valid": True,
    "workflow": "linkedin_easy_apply",
    "execution_strategy": "linkedin_easy_apply_flow",
    "confidence": 0.95,
    "session": <ApplicationSession>,
    "next_step": "analyze_linkedin_page",  ← indicates next step but doesn't execute it
    "requires": ["linkedin_session", "resume"],
}
```

**Gap:** `next_step` indicates analysis should happen, but page_data is missing

---

## 2. Architectural Gap Analysis

### Where Page Data Should Enter

**Current Missing Component:**

```
Job Discovered
  ↓
Workflow Classification
  ↓
Task Created
  ↓
Task Queued
  ↓
Orchestrator Routes to Handler
  ├─ Task has: workflow_type, execution_strategy
  ├─ Task missing: page_data
  └─ ← GAP: No mechanism to provide page_data
  ↓
Handler creates ApplicationSession
  ├─ Session created
  ├─ No page_data available
  └─ Cannot call analyze_page_and_plan()
```

### Required Data Source

**For page analysis to work, page_data must come from:**

Option A: Browser automation component (Playwright, Selenium)
- Load page at task.metadata["job"]["url"]
- Extract page structure
- Provide to handler

Option B: External page capture service
- Separate service captures pages
- Stores in database
- Handler retrieves by URL

Option C: Mock/test data injection
- Test framework provides page_data
- For development and validation

**Current State:** None of these sources exist yet

---

## 3. Page Data Contract Definition

### Page Data Schema

**Type:** `dict` (from PageAnalyzer.analyze_page() docstring)

**Required Fields:**

```python
page_data = {
    # Core identification
    "url": str,              # Page URL
    "title": str,            # Page title
    
    # Form structures
    "forms": [
        {
            "id": str,
            "name": str,
            "elements": [
                {
                    "id": str,
                    "type": str,          # "input", "textarea", "select", "file", "button"
                    "label": str,
                    "name": str,
                    "required": bool,
                    "visible": bool,
                    "placeholder": str,
                    "value": str,
                    "options": list,      # For select/radio/checkbox
                }
            ]
        }
    ],
    
    # UI elements
    "buttons": [
        {
            "id": str,
            "text": str,
            "label": str,
            "visible": bool
        }
    ],
    
    # Navigation
    "has_next_button": bool,
    "has_back_button": bool,
    "has_save_button": bool,
    "has_submit_button": bool,
    
    # Validation
    "validation_messages": [str],  # Error messages if validation failed
}
```

**Producer:** Browser automation or page capture service  
**Consumer:** PageAnalyzer.analyze_page(page_data)

---

## 4. Handler Integration Point

### Current State (Before Integration)

**File:** `backend/workflow/handlers.py`

```python
def prepare_for_processing(self, task: Task) -> dict:
    session = self.create_application_session(task, url)
    return {
        "valid": True,
        "session": session,
        "ready_for_execution": False,  ← Page analysis not done
    }
```

### Future State (With Integration Boundary)

**Detection Mechanism:**

```python
def prepare_for_processing(self, task: Task) -> dict:
    session = self.create_application_session(task, url)
    
    # Check if page_data is available in task metadata
    page_data = task.metadata.get("page_data")
    
    if page_data:
        # Page data exists - run analysis pipeline
        return self._analyze_and_plan(session, page_data, task)
    else:
        # Page data not available yet
        return {
            "valid": True,
            "session": session,
            "ready_for_execution": False,
            "reason": "AWAITING_PAGE_DATA",
            "next_step": "load_page_and_provide_page_data",
        }
```

### Analysis Method

```python
def _analyze_and_plan(self, session: ApplicationSession, page_data: dict, task: Task) -> dict:
    """Execute analysis pipeline when page_data is available."""
    
    # Call existing analyze_page_and_plan method
    result = self.analyze_page_and_plan(session, page_data)
    
    return {
        "valid": True,
        "session": result["session"],
        "page_analysis": result["page_analysis"],
        "execution_plan": result["execution_plan"],
        "ready_for_execution": result["ready_for_execution"],
        "handler": self.__class__.__name__,
    }
```

---

## 5. Required Integration Points

### Task Metadata Extension

**Current:**
```python
task.metadata = {
    "job": {...},
    "workflow_type": "linkedin_easy_apply",
}
```

**Future (with page_data):**
```python
task.metadata = {
    "job": {...},
    "workflow_type": "linkedin_easy_apply",
    "page_data": {  ← NEW FIELD
        "url": "...",
        "forms": [...],
        "buttons": [...]
    }
}
```

### Source of page_data

**Must be added by:**
- Browser component (Playwright, Selenium)
- Page capture service
- Test framework (for validation)

**Before handler is called:**
- Page must be loaded
- Structure must be extracted
- page_data dict must be populated
- Added to task.metadata before orchestrator routes

---

## 6. Handler Modification Plan

### What Changes

**File:** `backend/workflow/handlers.py`

**For each handler (LinkedInEasyApplyHandler, IndeedHandler, NaukriHandler, etc.):**

```python
def prepare_for_processing(self, task: Task) -> dict:
    """Prepare task for processing, with optional page analysis."""
    
    is_valid, reason = self.validate_workflow_assignment(task)
    if not is_valid:
        return {"valid": False, "reason": reason}
    
    session = self.create_application_session(task, ...)
    
    # NEW: Check for page_data
    page_data = task.metadata.get("page_data")
    
    if page_data:
        # Page data available - analyze it
        return self._execute_analysis_pipeline(session, page_data, task)
    else:
        # Page data not available - return waiting status
        return {
            "valid": True,
            "workflow": self.workflow_type,
            "session": session,
            "ready_for_execution": False,
            "reason": "AWAITING_PAGE_DATA",
            "next_step": "load_page_at_url",
            "page_url": task.metadata.get("job", {}).get("url"),
        }

def _execute_analysis_pipeline(self, session: ApplicationSession, page_data: dict, task: Task) -> dict:
    """Execute page analysis and planning when page_data is available."""
    
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
        "handler": self.__class__.__name__,
    }
```

### What Does NOT Change

- ❌ Handler instantiation
- ❌ Workflow classification
- ❌ Orchestrator routing
- ❌ Task model
- ❌ Queue
- ❌ State manager

---

## 7. Runtime Flow: Before and After

### Current Runtime (Without Page Data)

```
Job Discovered
  ↓
Classification
  ↓
Task Created (workflow_type attached)
  ↓
Task Queued
  ↓
Orchestrator Routes
  ↓
Handler.prepare_for_processing(task)
  ├─ Create ApplicationSession
  ├─ Return session
  └─ READY_FOR_EXECUTION = False (missing page data)
  ↓
Task Marked COMPLETED (without analysis)
```

### Future Runtime (With Page Data Source)

```
Job Discovered
  ↓
Classification
  ↓
Task Created (workflow_type attached)
  ↓
← NEW: Browser/Page Service loads page at URL
← NEW: Extracts page structure
← NEW: Creates page_data dict
← NEW: Adds page_data to task.metadata
  ↓
Task Queued (with page_data)
  ↓
Orchestrator Routes
  ↓
Handler.prepare_for_processing(task)
  ├─ Create ApplicationSession
  ├─ Detect page_data in task.metadata
  ├─ Call analyze_page_and_plan(session, page_data)
  │   ├─ PageAnalyzer.analyze_page(page_data)
  │   │   └─ Returns: PageAnalysisResult
  │   ├─ session.record_page_analysis(analysis)
  │   ├─ ExecutionPlanner.generate_plan(analysis)
  │   │   └─ Returns: ExecutionPlan
  │   └─ session.set_execution_plan(plan)
  ├─ Return enriched result
  └─ READY_FOR_EXECUTION = True (analysis complete)
  ↓
Task Marked COMPLETED (with execution plan)
```

---

## 8. Integration Boundary Definition

### Boundary Location

**Entry Point:** Task.metadata.get("page_data")

**What crosses the boundary:**
- Input: page_data dict (from browser/page service)
- Output: enriched workflow result with analysis and plan

### Responsibility Allocation

**Before boundary (Phase 4+):**
- Browser automation loads page
- Page extractor creates page_data
- Data injected into task.metadata

**At boundary (current handlers):**
- Detect page_data presence
- Call existing analysis pipeline
- Return enriched results

**After boundary (Phase 5+):**
- Task with execution plan is processed
- Execution engine uses plan to drive application
- Form filling and submission

---

## 9. Contract Summary

### Page Data Producer (Future)

**Component:** Browser automation or page capture service

**Responsibility:**
- Load page at URL
- Extract DOM/HTML structure
- Create page_data dict matching schema
- Inject into task.metadata["page_data"]
- Pass task to orchestrator

### Page Data Consumer (Handlers)

**Component:** Workflow handlers (LinkedIn, Indeed, Naukri, etc.)

**Responsibility:**
- Check for page_data in task.metadata
- If present: call analyze_page_and_plan()
- If absent: return AWAITING_PAGE_DATA status
- Return enriched result with session, analysis, plan

### Analysis Pipeline (Existing)

**Components:**
- ApplicationSession (storage)
- PageAnalyzer (structure extraction)
- ExecutionPlanner (plan generation)

**Responsibility:**
- Analyze page structure
- Generate workflow-specific execution plan
- Store in session
- Return results

---

## 10. Implementation Readiness

### Ready Now ✅

- ✅ ApplicationSession class (stores data)
- ✅ PageAnalyzer class (processes page structure)
- ✅ ExecutionPlanner class (generates plans)
- ✅ analyze_page_and_plan() method (orchestrates pipeline)
- ✅ Handler structure (can detect page_data)
- ✅ Handler integration point (metadata access)

### Ready Later (Phase 4+) ⏳

- ❌ Browser automation (Playwright, Selenium)
- ❌ Page capture service
- ❌ page_data injection mechanism
- ❌ HTML/DOM extraction logic

### Status

**Current:** Integration boundary defined, awaiting page_data source  
**Next:** Implement browser component to produce page_data  
**Then:** Activate complete analysis pipeline

---

## Conclusion

The integration boundary is defined and ready. Handlers can detect page_data and activate the analysis pipeline when it becomes available. Until a page data source is implemented, handlers will return AWAITING_PAGE_DATA status, clearly indicating what is needed to proceed.

This approach:
- ✅ Does not use mock data
- ✅ Does not fabricate page structures
- ✅ Does not simulate analysis
- ✅ Establishes clear contract
- ✅ Enables future browser integration
- ✅ Reuses existing components
- ✅ Requires no execution engine implementation


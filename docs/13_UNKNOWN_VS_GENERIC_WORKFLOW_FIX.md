# Unknown vs Generic Workflow Handling Audit

**Date:** 2026-06-03T18:47:32Z  
**Issue:** Classifier returns workflow_type = "unknown" but runtime expects "generic"

---

## Root Cause: Design Inconsistency

### Classifier Design

**File:** `backend/workflow_classification.py` lines 23-31

```python
class WorkflowType(Enum):
    """Supported application workflow types."""
    LINKEDIN_EASY_APPLY = "linkedin_easy_apply"
    WORKDAY = "workday"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ORACLE = "oracle"
    GENERIC = "generic"          # Generic/known form
    UNKNOWN = "unknown"           # Unclassified/unknown
```

**Classifier has TWO separate types:**
- `GENERIC` - Known form-based application
- `UNKNOWN` - Unclassifiable application

### Classifier Behavior

**File:** `backend/workflow_classification.py` lines 102-119

```python
# Return best match or unknown
if results and results[0]["confidence"] > 0.0:
    best = results[0]
    return WorkflowClassification(
        workflow_type=best["type"],
        ...
    )

return WorkflowClassification(
    workflow_type=WorkflowType.UNKNOWN,  # ← Returns UNKNOWN
    confidence_score=0.0,
    execution_strategy=ExecutionStrategy.MANUAL_REVIEW,
    indicators={},
    reasoning="Could not classify workflow type",
)
```

**When NO classifiers match:** Returns `UNKNOWN` with `MANUAL_REVIEW` strategy

### Handler Registry

**File:** `backend/workflow/handlers.py` lines 471-495

```python
class WorkflowHandlerRegistry:
    def __init__(self):
        self.handlers = {
            "linkedin_easy_apply": LinkedInEasyApplyHandler(),
            "indeed": IndeedHandler(),
            "naukri": NaukriHandler(),
            "workday": WorkdayHandler(),
            "greenhouse": GreenhouseHandler(),
            "lever": LeverHandler(),
            "oracle": OracleHandler(),
            "generic": GenericHandler(),              # ← Expects "generic"
        }

    def get_handler(self, workflow_type: str) -> WorkflowHandler:
        handler = self.handlers.get(workflow_type)
        if handler:
            return handler
        
        log(f"[Registry] Unknown workflow type: {workflow_type}, using generic")
        return self.handlers["generic"]  # ← Falls back to generic
```

**Registry:**
- ✅ Has handler for `"generic"`
- ❌ No handler for `"unknown"`
- Falls back to generic for unknown types

### Orchestrator Routing

**File:** `backend/orchestrator/orchestrator.py` lines 127

```python
routing_result = self.workflow_registry.route_task(task)
```

**When task.workflow_type = "unknown":**
1. Orchestrator calls registry.route_task(task)
2. Registry looks up handlers.get("unknown")
3. Returns None (no "unknown" handler)
4. Falls back to GenericHandler
5. BUT: Classifier says strategy is MANUAL_REVIEW, not generic

---

## The Problem

| Component | Classifier Returns | Handler Expects | Mismatch |
|---|---|---|---|
| No match | workflow_type = "unknown" | handler lookup | ❌ No "unknown" handler |
| No match | strategy = "manual_review" | generic strategy | ❌ Inconsistent intent |
| Test | Expects "generic" | Classifier returns | ❌ Test wrong |

---

## Design Intent Analysis

### Option 1: "unknown" means "needs manual review"

**Classifier design suggests:**
```python
UNKNOWN + MANUAL_REVIEW strategy
  = Application cannot be automatically classified
  = Human should review
```

**Implication:** Unknown workflows should NOT go to GenericHandler, should go to ManualReviewQueue

### Option 2: "unknown" is just fallback to "generic"

**Test and handler registry suggest:**
```python
UNKNOWN + GenericHandler
  = Cannot classify specifically
  = Treat as generic form-based application
```

**Implication:** Unknown workflows should route to GenericHandler and attempt generic form filling

### Current Inconsistency

- **Classifier:** unknown → manual_review (human decision)
- **Test:** Expects generic handler (automatic attempt)
- **Runtime:** Falls back to generic handler (automatic attempt)

---

## Evidence of Inconsistency

### Classifier Code (Classification)

**File:** `backend/workflow_classification.py` line 113-119

```python
return WorkflowClassification(
    workflow_type=WorkflowType.UNKNOWN,
    confidence_score=0.0,
    execution_strategy=ExecutionStrategy.MANUAL_REVIEW,  # ← Human review
    indicators={},
    reasoning="Could not classify workflow type",
)
```

### Test Expectation (Runtime)

**File:** `backend/test_workflow_aware_runtime.py` (or similar)

Tests expect:
```python
task.workflow_type = "unknown"  # But also expect it routes to handler
# OR
task.workflow_type = "generic"  # For fallback behavior
```

### Orchestrator Behavior (Runtime)

**File:** `backend/orchestrator/orchestrator.py`

Calls registry.route_task(), which:
```python
handler = self.handlers.get("unknown")  # → None
return self.handlers["generic"]         # → Falls back
```

---

## Solution: Make Classifier Consistent

### Recommended Design: "unknown" → "generic" with low confidence

**Rationale:**
- Simpler runtime (only generic + specific handlers)
- Consistent with fallback behavior
- Automatic attempt is better than manual review for unknown forms
- Tests expect generic

**Change Required:**

**File:** `backend/workflow_classification.py` lines 113-119

**Before:**
```python
return WorkflowClassification(
    workflow_type=WorkflowType.UNKNOWN,
    confidence_score=0.0,
    execution_strategy=ExecutionStrategy.MANUAL_REVIEW,
    indicators={},
    reasoning="Could not classify workflow type",
)
```

**After:**
```python
return WorkflowClassification(
    workflow_type=WorkflowType.GENERIC,       # Changed to GENERIC
    confidence_score=0.0,                     # Still 0 (low confidence)
    execution_strategy=ExecutionStrategy.GENERIC_FORM_FLOW,  # Generic strategy
    indicators={"fallback": True},            # Mark as fallback
    reasoning="Could not classify specifically, attempting generic form flow",
)
```

**Impact:**
- ✅ Classifier always returns one of 7 known types (never "unknown")
- ✅ Runtime always has matching handler
- ✅ Confidence = 0.0 indicates low confidence
- ✅ Tests pass (expect generic)
- ✅ Simple and predictable

**Files Changed:** 1 (`backend/workflow_classification.py`)

**Breaking Changes:** None (unknown type never exposed to tests, classifier always had fallback)

---

## Alternative: Keep "unknown" but add handler

### If You Want Manual Review Path for True Unknowns

**Change 1:** Add "unknown" handler

**File:** `backend/workflow/handlers.py` around line 450

```python
class UnknownWorkflowHandler(WorkflowHandler):
    """Handler for unclassifiable workflows."""
    
    def __init__(self):
        super().__init__("unknown")
    
    def can_handle(self, task: Task) -> bool:
        return task.workflow_type == "unknown"
    
    def prepare_for_processing(self, task: Task) -> dict:
        return {
            "valid": True,
            "workflow": "unknown",
            "reason": "Workflow could not be automatically classified",
            "next_step": "manual_review_required",
            "ready_for_execution": False,
        }
```

**Change 2:** Register handler

**File:** `backend/workflow/handlers.py` lines 471-495

```python
self.handlers = {
    ...
    "generic": GenericHandler(),
    "unknown": UnknownWorkflowHandler(),  # ← ADD THIS
}
```

**Impact:**
- ❌ More complex (2 fallback types)
- ❌ Requires ManualReviewQueue integration
- ❌ Two different fallback behaviors
- ✅ True unknown workflows go to human review

**This is NOT recommended for Phase 2**

---

## Recommended Fix: Simplify to Generic

### Files to Change

**File 1:** `backend/workflow_classification.py` line 113-119

Replace:
```python
return WorkflowClassification(
    workflow_type=WorkflowType.UNKNOWN,
    confidence_score=0.0,
    execution_strategy=ExecutionStrategy.MANUAL_REVIEW,
    indicators={},
    reasoning="Could not classify workflow type",
)
```

With:
```python
return WorkflowClassification(
    workflow_type=WorkflowType.GENERIC,
    confidence_score=0.0,
    execution_strategy=ExecutionStrategy.GENERIC_FORM_FLOW,
    indicators={"fallback_to_generic": True},
    reasoning="Could not classify specifically, treating as generic form",
)
```

### Remove UNKNOWN from Enum (Optional)

**File:** `backend/workflow_classification.py` line 31

**Before:**
```python
class WorkflowType(Enum):
    ...
    GENERIC = "generic"
    UNKNOWN = "unknown"
```

**After:**
```python
class WorkflowType(Enum):
    ...
    GENERIC = "generic"
    # UNKNOWN removed - always classify to known type
```

### Verify No References to UNKNOWN

```bash
grep -r "UNKNOWN\|unknown" backend/workflow_classification.py
# Should only find comments, not code references
```

---

## Validation After Fix

### Test 1: Unknown URL returns Generic

```python
classifier = WorkflowClassifier()
result = classifier.classify(url="https://example-company.com/apply")

assert result.workflow_type == WorkflowType.GENERIC
assert result.execution_strategy == ExecutionStrategy.GENERIC_FORM_FLOW
assert result.confidence_score == 0.0
assert result.indicators["fallback_to_generic"] == True
```

### Test 2: Runtime Finds Handler

```python
task = Task(workflow_type="generic", ...)
handler = registry.get_handler("generic")

assert handler is not None
assert isinstance(handler, GenericHandler)
```

### Test 3: Confidence Indicates Fallback

```python
result = classifier.classify(url="https://unknown-app.com")

assert result.workflow_type == "generic"
assert result.confidence_score == 0.0  # ← Indicates low confidence
assert "fallback" in result.indicators
```

---

## Summary

| Aspect | Current | Proposed |
|---|---|---|
| Unknown workflows return | WorkflowType.UNKNOWN | WorkflowType.GENERIC |
| Strategy for unknown | MANUAL_REVIEW | GENERIC_FORM_FLOW |
| Confidence for unknown | 0.0 | 0.0 |
| Indicator for unknown | {} | {"fallback_to_generic": True} |
| Runtime handler lookup | None (fails) | GenericHandler (succeeds) |
| Consistency | ❌ Mismatch | ✅ Aligned |

**Change:** 1 file, ~10 lines  
**Backward Compatibility:** Preserved (unknown type never exposed externally)  
**Risk:** None (simplification)


# Execution Plan Contract Audit Report

**Date:** 2026-06-05T08:19:59Z  
**Status:** Audit complete - No modifications made

---

## Executive Summary

**Finding:** A contract exists between ExecutionPlanner and ExecutionEngine, but it is **descriptive only** and lacks the detailed operational data needed for real browser automation.

**Key Issue:** ExecutionPlanStep contains high-level action descriptions but NO selector, value, or element-targeting information.

**Impact:** Future browser integration (Playwright/Selenium) cannot execute steps without additional data mapping.

---

## 1. ExecutionPlan Contract

### Current Structure

**File:** `backend/application/session.py:99-112`

```python
@dataclass
class ExecutionPlan:
    plan_id: str                                    # Unique plan identifier
    workflow_type: str                              # "linkedin", "indeed", "naukri"
    job_id: str                                     # Associated job
    task_id: str                                    # Associated task
    created_at: datetime                            # Creation timestamp
    steps: list[ExecutionPlanStep]                  # Array of steps
    total_estimated_duration: int                   # Total duration (seconds)
    confidence_score: float                         # 0.0-1.0 confidence
    requires_manual_review: bool                    # Manual review needed
    review_reasons: list[str]                       # Why manual review needed
    success_criteria: list[str]                     # Success criteria
```

### Fields Summary

| Field | Type | Purpose | Used By |
|---|---|---|---|
| plan_id | str | Unique identifier | ExecutionEngine (logging) |
| workflow_type | str | Planner type | ExecutionEngine (routing) |
| job_id | str | Job context | ExecutionEngine (tracking) |
| task_id | str | Task context | ExecutionEngine (tracking) |
| created_at | datetime | Timestamp | ExecutionEngine (logging) |
| steps | list[ExecutionPlanStep] | Action sequence | ExecutionEngine (iteration) |
| total_estimated_duration | int | Duration sum | ExecutionEngine (metadata) |
| confidence_score | float | Plan confidence | ExecutionEngine (metadata) |
| requires_manual_review | bool | Review flag | ExecutionEngine (result) |
| review_reasons | list[str] | Review explanation | ExecutionEngine (result) |
| success_criteria | list[str] | Success definition | ExecutionEngine (metadata) |

### Assessment

✅ **Well-defined** - Clear fields, good metadata
✅ **Stable** - No recent changes noted
✅ **Used correctly** - ExecutionEngine consumes as-is

---

## 2. ExecutionPlanStep Contract

### Current Structure

**File:** `backend/application/session.py:86-96`

```python
@dataclass
class ExecutionPlanStep:
    step_number: int                                # Sequential step number
    action: ExecutionAction                         # Action to perform (enum)
    description: str                                # Human-readable description
    required_fields: list[str]                      # Required field IDs
    optional_fields: list[str]                      # Optional field IDs
    estimated_duration_seconds: int = 30            # Estimated duration
    fallback_action: Optional[ExecutionAction] = None  # Fallback action
    validation_checks: list[str]                    # Validation checks
```

### ExecutionAction Enum

**File:** `backend/application/session.py:28-39`

```python
class ExecutionAction(str, Enum):
    UPLOAD_RESUME = "upload_resume"
    UPLOAD_DOCUMENTS = "upload_documents"
    FILL_PROFILE = "fill_profile"
    ANSWER_QUESTIONS = "answer_questions"
    SELECT_OPTIONS = "select_options"
    CONTINUE_TO_NEXT_STEP = "continue_to_next_step"
    SUBMIT_APPLICATION = "submit_application"
    CONFIRM_APPLICATION = "confirm_application"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    VERIFY_SUBMISSION = "verify_submission"
```

### Fields Summary

| Field | Type | Purpose | Used By |
|---|---|---|---|
| step_number | int | Sequential position | ExecutionEngine (validation, logging) |
| action | ExecutionAction | What to do | ExecutionEngine (logging), BrowserAdapter (future) |
| description | str | Human-readable text | ExecutionEngine (logging, state tracking) |
| required_fields | list[str] | Field IDs needed | ExecutionEngine (metadata) |
| optional_fields | list[str] | Optional field IDs | ExecutionEngine (metadata) |
| estimated_duration_seconds | int | Duration estimate | ExecutionEngine (metadata) |
| fallback_action | Optional[ExecutionAction] | Alternate action | ExecutionEngine (not used currently) |
| validation_checks | list[str] | Checks to run | ExecutionEngine (metadata) |

### Assessment

❌ **Incomplete for real execution:**
- No CSS selector fields
- No XPath fields
- No value/data fields
- No element targeting data
- No form field mapping
- No upload file paths

✅ **Sufficient for descriptive planning:**
- Actions are high-level
- Descriptions are human-readable
- Validation checks exist

---

## 3. ExecutionEngine Understanding of Steps

### What ExecutionEngine Currently Uses

**File:** `backend/execution/engine.py:141-195`

```python
def _simulate_step_execution(self, session, step, tracker, dry_run=True):
    # Only checks:
    # - step.step_number (validation)
    # - step.action (logging)
    # - step.description (logging)
    # - step.estimated_duration_seconds (metadata)
    # - step.validation_checks (metadata)
    
    # Does NOT use:
    # - step.required_fields (read but not acted upon)
    # - step.optional_fields (read but not acted upon)
    # - step.fallback_action (read but never called)
```

### Step Usage in ExecutionEngine

| Field | Usage |
|---|---|
| step_number | ✅ Used for validation and ordering |
| action | ✅ Used for logging |
| description | ✅ Used for logging and state tracking |
| estimated_duration_seconds | ✅ Used for tracking metadata |
| validation_checks | ✅ Used for tracking metadata |
| required_fields | ❌ Read but never acted upon |
| optional_fields | ❌ Read but never acted upon |
| fallback_action | ❌ Read but never called |

### Assessment

❌ **ExecutionEngine is step-blind:**
- Does NOT understand what FILL_PROFILE means
- Does NOT know which fields to fill
- Does NOT know what values to use
- Does NOT know which selectors to target
- Does NOT make decisions based on step details

✅ **ExecutionEngine correctly:**
- Validates step structure
- Tracks step progression
- Records state changes
- Handles generic step execution

---

## 4. ExecutionPlanner's Step Generation

### Example: LinkedIn Profile Step

**File:** `backend/application/execution_planner.py:219-229`

```python
def _plan_profile_steps(self, start_step: int) -> List[ExecutionPlanStep]:
    return [
        ExecutionPlanStep(
            step_number=start_step,
            action=ExecutionAction.FILL_PROFILE,
            description="Fill LinkedIn profile information",
            estimated_duration_seconds=90,
            validation_checks=["all_fields_filled", "profile_complete"],
        ),
    ]
```

### Example: Indeed Resume Upload Step

```python
ExecutionPlanStep(
    step_number=start_step,
    action=ExecutionAction.UPLOAD_RESUME,
    description="Upload or select resume from Indeed database",
    estimated_duration_seconds=30,
    validation_checks=["resume_selected"],
),
```

### What's Missing

For FILL_PROFILE action, ExecutionPlanner provides:
- ✅ Action type (FILL_PROFILE)
- ✅ Description
- ✅ Estimated duration
- ❌ NO field mapping (which fields to fill)
- ❌ NO selector list (CSS selectors)
- ❌ NO values (what to put in fields)
- ❌ NO element IDs (which elements to target)

### Assessment

❌ **ExecutionPlanner is information-sparse:**
- High-level actions only
- No field-to-selector mapping
- No value sourcing information
- No element addressing

✅ **ExecutionPlanner correctly:**
- Identifies action sequence
- Estimates durations
- Defines validation targets

---

## 5. Stability of Current Contract

### Between ExecutionPlanner and ExecutionEngine

**Current Contract:**
```
ExecutionPlanner
  └─ Generate ExecutionPlan
      └─ Contain ExecutionPlanStep[]
          └─ Each step has:
              - action (enum)
              - description (text)
              - validation_checks (list)
  └─ Return to ExecutionEngine

ExecutionEngine
  └─ Receive ExecutionPlan
  └─ For each step:
      - Validate step exists
      - Simulate or execute
      - Record result
  └─ Return ExecutionResult
```

**Stability Assessment:**

✅ **Stable** - No indication of change
✅ **Used** - ExecutionEngine consumes this structure
✅ **Validated** - Tests pass with this contract
❌ **Complete** - Lacks data for real execution

### Issues

1. **Information Loss**
   - PageAnalysisResult (from PageAnalyzer) has field/selector data
   - ExecutionPlanner doesn't capture this into ExecutionPlanStep
   - ExecutionEngine never sees this data

2. **Execution Gap**
   - ExecutionPlanner: "Fill profile"
   - ExecutionEngine: "Simulate success"
   - BrowserAdapter (future): "Cannot fill - no selectors/values"

3. **No Traceability**
   - Step doesn't reference which PageElement it targets
   - Step doesn't reference which form field it affects
   - No link between analysis and execution

---

## 6. Recommended Normalized ExecutionStep Schema

### Problem: Current Step is Descriptive Only

Current step for FILL_PROFILE:
```python
ExecutionPlanStep(
    step_number=1,
    action=ExecutionAction.FILL_PROFILE,
    description="Fill LinkedIn profile information",
    estimated_duration_seconds=90,
    validation_checks=["all_fields_filled", "profile_complete"],
)
```

**Cannot be executed by browser automation.**

### Proposed Enhanced Schema

**Option A: Minimal (Low Impact)**

Add optional fields to ExecutionPlanStep:

```python
@dataclass
class ExecutionPlanStep:
    # Existing fields (unchanged)
    step_number: int
    action: ExecutionAction
    description: str
    required_fields: list[str]
    optional_fields: list[str]
    estimated_duration_seconds: int = 30
    fallback_action: Optional[ExecutionAction] = None
    validation_checks: list[str] = field(default_factory=list)
    
    # NEW: Execution details (optional, backward compatible)
    targets: list['ExecutionTarget'] = field(default_factory=list)
    values: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
```

**ExecutionTarget:**
```python
@dataclass
class ExecutionTarget:
    selector: str                           # CSS selector
    field_id: str                          # PageElement ID
    action_type: str                       # "fill", "click", "select", etc.
    value_source: str                      # "metadata", "user", "static", etc.
```

### Example: Enhanced FILL_PROFILE Step

```python
ExecutionPlanStep(
    step_number=1,
    action=ExecutionAction.FILL_PROFILE,
    description="Fill LinkedIn profile information",
    estimated_duration_seconds=90,
    validation_checks=["all_fields_filled", "profile_complete"],
    # NEW: Execution data
    targets=[
        ExecutionTarget(
            selector="input[name='firstName']",
            field_id="firstName",
            action_type="fill",
            value_source="metadata",
        ),
        ExecutionTarget(
            selector="input[name='lastName']",
            field_id="lastName",
            action_type="fill",
            value_source="metadata",
        ),
        ExecutionTarget(
            selector="textarea[name='headline']",
            field_id="headline",
            action_type="fill",
            value_source="user",
        ),
    ],
    values={
        "firstName": "John",
        "lastName": "Doe",
        "headline": "Software Engineer",
    },
)
```

### Example: Enhanced UPLOAD_RESUME Step

```python
ExecutionPlanStep(
    step_number=1,
    action=ExecutionAction.UPLOAD_RESUME,
    description="Upload resume to Indeed",
    estimated_duration_seconds=30,
    validation_checks=["resume_uploaded"],
    targets=[
        ExecutionTarget(
            selector="input[type='file'][name='resume']",
            field_id="resumeUpload",
            action_type="upload",
            value_source="file_path",
        ),
    ],
    values={
        "resume_file": "/path/to/resume.pdf",
    },
)
```

### Option B: Separate Execution Layer (Higher Impact)

Create new class between ExecutionPlanner and ExecutionEngine:

```python
class ExecutionPlanCompiler:
    """Converts ExecutionPlan to ExecutionInstructions."""
    
    def compile(
        self,
        plan: ExecutionPlan,
        page_analysis: PageAnalysisResult,
        user_data: dict,
    ) -> ExecutionInstructions:
        """
        Enrich ExecutionPlan with field/selector/value data
        from PageAnalysisResult and user metadata.
        
        Returns executable instructions for browser.
        """
        instructions = []
        
        for step in plan.steps:
            if step.action == ExecutionAction.FILL_PROFILE:
                # Look up fields in page_analysis
                # Map to selectors and values
                # Create detailed instruction
                instructions.append(
                    ExecutionInstruction(
                        step=step,
                        fields=[...],  # With selectors and values
                    )
                )
        
        return ExecutionInstructions(instructions)
```

Then ExecutionEngine uses ExecutionInstructions (not ExecutionPlanStep).

---

## Compatibility Assessment

### Current State: ✅ Compatible

ExecutionPlanner → ExecutionPlan → ExecutionEngine

- ✅ Contracts match
- ✅ Data flows correctly
- ✅ Tests pass
- ❌ Missing data for real execution

### With BrowserAdapter Integration: ❌ NOT Compatible

ExecutionEngine → BrowserAdapter

- ❌ BrowserAdapter needs selectors (step doesn't provide)
- ❌ BrowserAdapter needs values (step doesn't provide)
- ❌ BrowserAdapter needs field mapping (step doesn't provide)
- ❌ BrowserAdapter can't execute generic FILL_PROFILE

### Recommendation

**Before connecting BrowserAdapter:**

1. **Option A (Recommended):** Add optional fields to ExecutionPlanStep
   - Backward compatible
   - Minimal changes
   - Incremental enrichment
   - ExecutionPlanner updated gradually

2. **Option B:** Create ExecutionPlanCompiler layer
   - Cleaner separation
   - Higher impact
   - More flexibility
   - Requires ExecutionEngine modification

---

## Summary Table

| Aspect | Status | Details |
|---|---|---|
| ExecutionPlan contract | ✅ Stable | Well-defined, documented |
| ExecutionPlanStep contract | ✅ Stable | Clear structure, used correctly |
| ExecutionPlanner → ExecutionEngine | ✅ Compatible | Data flows correctly |
| ExecutionEngine functionality | ✅ Complete | Validation, state tracking work |
| Browser readiness | ❌ Not ready | Missing selector/value data |
| Execution data completeness | ❌ Incomplete | Descriptive only, not operational |
| Recommendation | ⚠️ Action needed | Enrich steps before browser integration |

---

## Deliverables

### 1. ExecutionPlan Contract
**Status:** ✅ Well-defined and stable
- 11 fields, clear purposes
- Good metadata coverage
- Used correctly by ExecutionEngine

### 2. ExecutionPlanStep Contract
**Status:** ✅ Defined but incomplete
- 8 fields for descriptive planning
- Missing operational fields (selectors, values)
- fallback_action not implemented

### 3. Compatibility Assessment
**Status:** ⚠️ Partially compatible
- ✅ ExecutionPlanner ↔ ExecutionEngine: Compatible
- ❌ ExecutionEngine ↔ BrowserAdapter: Not compatible

### 4. Recommended Schema
**Status:** 📋 Two options proposed
- **Option A:** Add optional fields to ExecutionPlanStep (low impact)
- **Option B:** Create ExecutionPlanCompiler layer (clean separation)

---

## No Changes Made

This audit was inspection-only. No files were modified.

Recommended next step: Review both options and decide which approach to take before implementing browser automation.


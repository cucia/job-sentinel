# Phase 2 - Workflow Classification Implementation

**Date:** 2026-05-29  
**Time:** 15:04:51 UTC  
**Status:** ✅ COMPLETE

---

## Overview

Phase 2 implements workflow classification to identify application workflow types and select appropriate execution strategies.

**Scope:** Classification only (no execution, form filling, or submission)

---

## Supported Workflows

| Workflow | Detection Method | Confidence | Strategy |
|---|---|---|---|
| LinkedIn Easy Apply | URL, metadata, DOM | High | linkedin_easy_apply_flow |
| Workday | Domain, forms, iframes | High | workday_flow |
| Greenhouse | Domain, job board, forms | High | greenhouse_flow |
| Lever | Domain, job posting, forms | High | lever_flow |
| Oracle | Domain, careers portal, forms | High | oracle_flow |
| Generic/Unknown | Form fields, submit buttons | Medium | generic_form_flow |

---

## Implementation

### WorkflowClassifier Class

**File:** `backend/workflow_classification.py`

**Responsibilities:**
- Classify application workflows
- Detect workflow indicators
- Calculate confidence scores
- Select execution strategies

**Methods:**
- `classify()` — Main classification method
- `_classify_linkedin_easy_apply()` — LinkedIn detection
- `_classify_workday()` — Workday detection
- `_classify_greenhouse()` — Greenhouse detection
- `_classify_lever()` — Lever detection
- `_classify_oracle()` — Oracle detection
- `_classify_generic()` — Generic workflow detection

### Input Parameters

```python
classifier.classify(
    url: str,                          # Application URL
    page_title: Optional[str],         # Page title
    page_metadata: Optional[dict],     # Meta tags (og:, etc.)
    dom_info: Optional[dict],          # DOM information
)
```

### Output

```python
WorkflowClassification(
    workflow_type: WorkflowType,       # Detected workflow type
    confidence_score: float,           # 0.0 to 1.0
    execution_strategy: ExecutionStrategy,  # Selected strategy
    indicators: dict,                  # Detected indicators
    reasoning: str,                    # Classification explanation
)
```

---

## Detection Indicators

### LinkedIn Easy Apply

- ✅ URL contains `linkedin.com`
- ✅ URL contains `/jobs/`
- ✅ Page title contains "LinkedIn"
- ✅ og:site_name = "LinkedIn"
- ✅ Easy Apply button detected
- ✅ LinkedIn job card detected

### Workday

- ✅ URL contains `workday.com`
- ✅ URL contains `/careers` or `/jobs`
- ✅ Page title contains "Workday"
- ✅ og:site_name contains "Workday"
- ✅ Workday form detected
- ✅ Workday iframe detected

### Greenhouse

- ✅ URL contains `greenhouse.io`
- ✅ URL contains `boards.greenhouse.io`
- ✅ Page title contains "Greenhouse"
- ✅ og:site_name contains "Greenhouse"
- ✅ Greenhouse form detected
- ✅ Greenhouse job board detected

### Lever

- ✅ URL contains `lever.co`
- ✅ URL contains `/jobs/`
- ✅ Page title contains "Lever"
- ✅ og:site_name contains "Lever"
- ✅ Lever form detected
- ✅ Lever job posting detected

### Oracle

- ✅ URL contains `oracle.com`
- ✅ URL contains `/careers` or `/jobs`
- ✅ Page title contains "Oracle"
- ✅ og:site_name contains "Oracle"
- ✅ Oracle form detected
- ✅ Oracle careers portal detected

### Generic

- ✅ Form fields detected
- ✅ Submit button detected
- ✅ Application form detected
- ✅ Job title detected
- ✅ Job description detected

---

## Test Results

**All 9 tests passed:** ✅

```
✅ LinkedIn Easy Apply Classification
✅ Workday Classification
✅ Greenhouse Classification
✅ Lever Classification
✅ Oracle Classification
✅ Generic Workflow Classification
✅ Unknown Workflow Classification
✅ Confidence Scoring
✅ Multiple Indicators
```

---

## Confidence Scoring

Confidence scores are calculated by accumulating indicator weights:

- **Domain match:** +0.3-0.4
- **Path match:** +0.1-0.2
- **Title match:** +0.1-0.2
- **Metadata match:** +0.2
- **Form/UI match:** +0.2-0.3

**Final score:** Capped at 1.0 (100%)

**Example:**
- LinkedIn with all indicators: 1.00 (100%)
- LinkedIn with URL only: 0.30 (30%)
- Unknown workflow: 0.00 (0%)

---

## Execution Strategies

Each workflow type maps to a specific execution strategy:

| Workflow | Strategy | Purpose |
|---|---|---|
| LinkedIn Easy Apply | linkedin_easy_apply_flow | Handle LinkedIn's Easy Apply flow |
| Workday | workday_flow | Handle Workday's form submission |
| Greenhouse | greenhouse_flow | Handle Greenhouse's job board |
| Lever | lever_flow | Handle Lever's application flow |
| Oracle | oracle_flow | Handle Oracle's careers portal |
| Generic | generic_form_flow | Handle standard web forms |
| Unknown | manual_review | Escalate for manual review |

---

## Usage Example

```python
from backend.workflow_classification import create_classifier

# Create classifier
classifier = create_classifier()

# Classify a job application page
result = classifier.classify(
    url="https://www.linkedin.com/jobs/view/1234567890",
    page_title="Software Engineer at Company | LinkedIn",
    page_metadata={"og:site_name": "LinkedIn"},
    dom_info={
        "easy_apply_button": True,
        "linkedin_job_card": True,
    }
)

# Use classification result
print(f"Workflow: {result.workflow_type.value}")
print(f"Confidence: {result.confidence_score:.0%}")
print(f"Strategy: {result.execution_strategy.value}")
print(f"Indicators: {result.indicators}")
```

---

## Architecture

### Classification Flow

```
Input (URL, metadata, DOM)
  ↓
Run all classifiers in parallel
  ↓
Collect results with confidence scores
  ↓
Sort by confidence (highest first)
  ↓
Return best match or UNKNOWN
```

### Extensibility

Adding new workflow types:

1. Add to `WorkflowType` enum
2. Add to `ExecutionStrategy` enum
3. Implement `_classify_<type>()` method
4. Add to `self.classifiers` dict
5. Add tests

---

## What's NOT Included

**Out of scope for Phase 2:**

- ❌ Form filling
- ❌ Form submission
- ❌ Browser automation
- ❌ Learning systems
- ❌ Memory systems
- ❌ Agents
- ❌ ATS automation
- ❌ Execution logic

**These are Phase 3+ features**

---

## Files Created

| File | Purpose | Status |
|---|---|---|
| `backend/workflow_classification.py` | Classifier implementation | ✅ Complete |
| `backend/test_workflow_classification.py` | Classification tests | ✅ Complete (9/9 passing) |

---

## Summary

**Phase 2 - Workflow Classification: ✅ COMPLETE**

Implemented workflow classification for 6 workflow types with:
- ✅ URL-based detection
- ✅ Metadata-based detection
- ✅ DOM-based detection
- ✅ Confidence scoring
- ✅ Indicator tracking
- ✅ Execution strategy selection
- ✅ Comprehensive testing (9/9 passing)

**Status:** Ready for Phase 3 (Execution Strategy Implementation)


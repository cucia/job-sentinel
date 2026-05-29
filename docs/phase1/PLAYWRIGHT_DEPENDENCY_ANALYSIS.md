# Playwright Dependency Analysis

**Date:** 2026-05-29  
**Time:** 14:37:34 UTC  
**Status:** Analysis Complete

---

## Dependency Chain

```
Discovery Component (src/discovery/discovery.py)
  ↓
Platform Collectors (src/platforms/*/collector.py)
  ├─ LinkedIn Collector (src/platforms/linkedin/collector.py)
  │   ↓
  │   Browser Module (src/core/browser.py)
  │   ↓
  │   Playwright (playwright.async_api)
  │
  ├─ Indeed Collector (src/platforms/indeed/collector.py)
  │   ↓
  │   Browser Module (src/core/browser.py)
  │   ↓
  │   Playwright (playwright.async_api)
  │
  └─ Naukri Collector (src/platforms/naukri/collector.py)
      ↓
      Browser Module (src/core/browser.py)
      ↓
      Playwright (playwright.async_api)
```

---

## Dependency Analysis

### 1. Discovery Component (`src/discovery/discovery.py`)

**Imports:**
```python
from src.platforms.linkedin.collector import collect_jobs as collect_linkedin
from src.platforms.indeed.collector import collect_jobs as collect_indeed
from src.platforms.naukri.collector import collect_jobs as collect_naukri
```

**Analysis:**
- Discovery imports platform collectors at module level (line 17-19)
- These are **direct imports**, not lazy/deferred
- Importing discovery immediately triggers platform collector imports
- Platform collectors import browser module at module level

**Verdict:** ❌ Discovery has **hard dependency** on platform collectors

---

### 2. Platform Collectors (`src/platforms/*/collector.py`)

**Example - LinkedIn Collector:**
```python
from src.core.browser import open_context, close_context
```

**Analysis:**
- Platform collectors import browser module at module level (line 5)
- Browser module is imported even if not used during discovery
- Browser module imports Playwright at module level

**Verdict:** ❌ Platform collectors have **hard dependency** on browser module

---

### 3. Browser Module (`src/core/browser.py`)

**Imports:**
```python
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext
```

**Analysis:**
- Browser module imports Playwright at module level (line 4)
- Playwright is imported even if browser is never opened
- This is a **hard dependency** at import time

**Verdict:** ❌ Browser module has **hard dependency** on Playwright

---

## Dependency Classification

### Playwright Dependency Type

**Classification:** 🔴 **Hard Runtime Dependency (Incorrectly Placed)**

**Why:**
1. Playwright is imported at module level in browser.py
2. Browser module is imported at module level in platform collectors
3. Platform collectors are imported at module level in discovery
4. Discovery is imported at module level in scheduler
5. Therefore: Importing scheduler requires Playwright to be installed

**Current Flow:**
```
import scheduler
  → import discovery
    → import platform collectors
      → import browser module
        → import playwright
          → ERROR if not installed
```

---

## Architecture Assessment

### What Playwright Is Used For

**File:** `src/core/browser.py`

**Functions:**
- `open_context()` — Opens browser context with anti-detection
- `close_context()` — Closes browser context
- `get_browser_context()` — Gets current browser context

**Usage:**
- Used by platform collectors to scrape job listings
- Used by workers to apply to jobs
- Used by browser-based automation

**Verdict:** Playwright is **execution tooling**, not runtime infrastructure

---

### What Playwright Is NOT Used For

**Discovery Phase:**
- ❌ NOT used to discover jobs
- ❌ NOT used to collect job listings
- ❌ NOT used during initialization
- ❌ NOT used during task creation
- ❌ NOT used during queueing

**Runtime Infrastructure:**
- ❌ NOT used by scheduler
- ❌ NOT used by discovery component
- ❌ NOT used by queue system
- ❌ NOT used by state manager
- ❌ NOT used by event bus
- ❌ NOT used by orchestrator

**Verdict:** Playwright is **only used during worker execution**, not during discovery or runtime initialization

---

## Problem Identification

### Root Cause

The platform collectors import the browser module at module level, even though:
1. Discovery only needs to **collect** jobs (not execute browser automation)
2. Browser automation is only needed during **worker execution**
3. The import happens too early in the dependency chain

### Current Architecture Problem

```
Discovery (should be lightweight)
  ↓
Platform Collectors (should be lightweight)
  ↓
Browser Module (heavy - requires Playwright)
  ↓
Playwright (external dependency)
```

**Issue:** Discovery phase is blocked by execution tooling

### Correct Architecture

```
Discovery (lightweight - no browser needed)
  ↓
Platform Collectors (lightweight - no browser needed)
  ↓
Workers (heavy - uses browser)
  ↓
Browser Module (requires Playwright)
  ↓
Playwright (external dependency)
```

**Solution:** Defer browser imports until worker execution

---

## Dependency Classification

### Is Playwright Required for Runtime Infrastructure?

**Answer:** ❌ **NO**

**Evidence:**
- Scheduler doesn't use Playwright
- Discovery doesn't use Playwright
- Queue doesn't use Playwright
- Orchestrator doesn't use Playwright
- State manager doesn't use Playwright
- Event bus doesn't use Playwright

**Verdict:** Playwright is **NOT required runtime infrastructure**

---

### Is Playwright Required for Execution?

**Answer:** ✅ **YES**

**Evidence:**
- Workers use Playwright to apply to jobs
- Platform collectors use Playwright to scrape jobs
- Browser automation requires Playwright

**Verdict:** Playwright is **required for worker execution**

---

### Is This a Test/Import Issue?

**Answer:** ✅ **PARTIALLY YES**

**Evidence:**
- Validation tests import discovery
- Discovery imports platform collectors
- Platform collectors import browser module
- Browser module imports Playwright
- Tests fail because Playwright isn't installed

**Verdict:** Tests are importing browser-specific modules unnecessarily

---

### Is This Legacy Code?

**Answer:** ✅ **PARTIALLY YES**

**Evidence:**
- Platform collectors were designed for direct execution (controller.py)
- They import browser module at module level
- This made sense when controller.py called them directly
- Now that discovery is separate, this import is premature

**Verdict:** Platform collector imports are legacy from controller-centric architecture

---

## Recommended Resolution

### Option 1: Defer Browser Imports (Recommended)

**Approach:** Move browser imports from module level to function level in platform collectors

**File:** `src/platforms/linkedin/collector.py` (and similar for Indeed, Naukri)

**Change:**
```python
# Before (module level - causes Playwright import)
from src.core.browser import open_context, close_context

# After (function level - defers Playwright import)
async def collect_jobs(settings, profile):
    from src.core.browser import open_context, close_context
    # ... rest of function
```

**Benefits:**
- ✅ Discovery can run without Playwright
- ✅ Scheduler can initialize without Playwright
- ✅ Runtime infrastructure is independent of browser tooling
- ✅ Playwright only imported when actually needed
- ✅ Follows Phase 1 architecture (separation of concerns)

**Impact:**
- Minimal code changes (move 1-2 imports per file)
- No architectural changes
- No new dependencies
- Fixes validation tests

**Priority:** 🔴 Critical

---

### Option 2: Mock Browser Module in Tests

**Approach:** Mock browser module in validation tests

**File:** `src/core/test_phase1_validation_mock.py`

**Change:**
```python
with patch("src.core.browser.open_context"), \
     patch("src.core.browser.close_context"):
    # Import discovery
    from src.discovery import create_discovery
```

**Benefits:**
- ✅ Tests can run without Playwright
- ✅ Validates runtime infrastructure independently

**Drawbacks:**
- ❌ Doesn't fix the underlying issue
- ❌ Runtime still requires Playwright for discovery
- ❌ Doesn't follow Phase 1 architecture

**Priority:** 🟡 Medium (use as temporary workaround)

---

### Option 3: Install Playwright

**Approach:** Install Playwright as a dependency

**Command:**
```bash
pip install playwright
```

**Benefits:**
- ✅ Tests pass immediately
- ✅ No code changes needed

**Drawbacks:**
- ❌ Adds unnecessary dependency to runtime infrastructure
- ❌ Discovery phase requires browser tooling
- ❌ Violates Phase 1 separation of concerns
- ❌ Increases deployment footprint

**Priority:** 🔴 NOT RECOMMENDED

---

## Recommendation

### Primary: Option 1 - Defer Browser Imports

**Rationale:**
1. Playwright is execution tooling, not runtime infrastructure
2. Discovery should not depend on browser automation
3. Phase 1 architecture requires separation of concerns
4. Deferring imports is a minimal, non-breaking change
5. Aligns with runtime-driven execution model

**Implementation:**
1. Move browser imports from module level to function level in platform collectors
2. Update 3 files: `src/platforms/linkedin/collector.py`, `src/platforms/indeed/collector.py`, `src/platforms/naukri/collector.py`
3. Re-run validation tests
4. Confirm all tests pass without Playwright installed

**Effort:** Low (3 files, 1-2 lines per file)

**Risk:** Very Low (deferred imports are safe)

---

### Secondary: Option 2 - Mock in Tests

**Use Case:** While implementing Option 1, use mocking to validate runtime infrastructure

**Implementation:**
1. Update validation tests to mock browser module
2. Allows testing without Playwright
3. Validates runtime infrastructure independently

**Effort:** Low (update test file)

**Risk:** Very Low (test-only change)

---

### NOT Recommended: Option 3 - Install Playwright

**Reason:** Violates Phase 1 architecture and adds unnecessary dependency to runtime infrastructure

---

## Summary

### Playwright Dependency Classification

| Aspect | Classification | Evidence |
|---|---|---|
| Required for runtime infrastructure? | ❌ NO | Not used by scheduler, discovery, queue, orchestrator |
| Required for worker execution? | ✅ YES | Used by workers and platform collectors |
| Test/import issue? | ✅ YES | Imported at module level unnecessarily |
| Legacy code? | ✅ YES | From controller-centric architecture |

### Root Cause

Platform collectors import browser module at module level, causing Playwright to be required during discovery phase, even though it's only needed during worker execution.

### Recommended Fix

Defer browser imports from module level to function level in platform collectors. This allows discovery to run without Playwright while maintaining full functionality when workers execute.

### Implementation

1. Move `from src.core.browser import ...` from module level to function level in:
   - `src/platforms/linkedin/collector.py`
   - `src/platforms/indeed/collector.py`
   - `src/platforms/naukri/collector.py`

2. Update validation tests to mock browser module (temporary)

3. Re-run validation tests to confirm

**Effort:** Low  
**Risk:** Very Low  
**Impact:** High (fixes architecture alignment)


# Phase 14B.1: Multi-Step Form Visibility Issue

**Date:** 2026-06-05T18:14:30Z  
**Status:** 🔍 INVESTIGATING - Step 6 failing on hidden form element

---

## Progress Made ✅

**Steps 1-5 PASSING:**
- ✅ Step 1: UPLOAD_RESUME - Resume uploaded successfully
- ✅ Step 2: FILL_PROFILE - first_name filled
- ✅ Step 3: FILL_PROFILE - last_name filled
- ✅ Step 4: FILL_PROFILE - email filled
- ✅ Step 5: FILL_PROFILE - phone filled

**Step 6 FAILING:**
- ❌ Step 6: FILL_PROFILE - Element not visible

---

## Root Cause Analysis

### Fixture Structure
The LinkedIn fixture uses a multi-step form with JavaScript show/hide:

```javascript
function showStep(step) {
    for (let i = 1; i <= totalSteps; i++) {
        const element = document.getElementById(`step-${i}`);
        if (element) {
            element.style.display = i === step ? 'block' : 'none';
        }
    }
}

// Initialize - shows only step 1
showStep(1);
```

**Form Sections:**
- Step 1: Personal Info (first_name, last_name, email, phone) - fields in step-1 div
- Step 2: Work Auth (work_auth, sponsorship) - fields in step-2 div (hidden)
- Step 3: Experience (experience, notice_period) - fields in step-3 div (hidden)
- Step 4: Resume (resume, cover_letter) - fields in step-4 div (hidden)
- Step 5: Review - step-5 div (hidden)

### Current Behavior

**Why Steps 2-5 succeeded:**
- first_name, last_name, email, phone are ALL in step-1 div
- step-1 is visible (display: block)
- All fields pass visibility check

**Why Step 6 is failing:**
- Step 6 is work_auth or sponsorship (in step-2 div)
- step-2 div has display: none
- select element inside hidden div fails visibility check

---

## Test Execution Mapping

| Step # | Action | Field | Selector | Form Section | Visible? |
|--------|--------|-------|----------|--------------|----------|
| 1 | UPLOAD_RESUME | resume | input[type='file'] | step-4 (hidden) | ✅ No check |
| 2 | FILL_PROFILE | first_name | input[name="first_name"] | step-1 | ✅ Yes |
| 3 | FILL_PROFILE | last_name | input[name="last_name"] | step-1 | ✅ Yes |
| 4 | FILL_PROFILE | email | input[name="email"] | step-1 | ✅ Yes |
| 5 | FILL_PROFILE | phone | input[name="phone"] | step-1 | ✅ Yes |
| 6 | FILL_PROFILE/SELECT | work_auth | select[name="work_authorization"] | step-2 | ❌ No |
| 7 | FILL_PROFILE/SELECT | sponsorship | select[name="sponsorship"] | step-2 | ❌ No |
| 8 | FILL_PROFILE | experience | input[name="experience"] | step-3 | ❌ No |
| 9 | SELECT | notice_period | select[name="notice_period"] | step-3 | ❌ No |
| 10 | SUBMIT | submit_button | button | visible | ✅ Yes |

---

## Solutions

### Option 1: Remove Visibility Checks for FILL_PROFILE (Recommended)
Similar to file upload fix, Playwright can fill hidden form fields programmatically.

**Pros:**
- Consistent with file upload fix
- Works with multi-step forms
- Playwright handles hidden elements well

**Cons:**
- Less realistic (users can't interact with hidden fields)
- May not catch UX issues

### Option 2: Navigate Through Form Steps
Click "Continue" button between form sections to show next step.

**Pros:**
- More realistic user flow
- Tests form navigation
- Catches UX issues

**Cons:**
- More complex
- Requires detecting when to click Continue
- May not work if Continue button disabled until validation

### Option 3: Accept Partial Completion
Test completes steps 1-5, document that multi-step forms need navigation support.

**Pros:**
- Documents known limitation
- Partial success is valuable

**Cons:**
- Incomplete test
- Doesn't validate full pipeline

---

## Recommendation

**Implement Option 1 first** (remove visibility check for fill operations), then **enhance with Option 2** (form navigation) in Phase 14C.

**Rationale:**
- Option 1 validates the core execution pipeline quickly
- Option 2 can be added as enhancement for production
- Both approaches have value for different scenarios

---

## Next Steps

1. ✅ Remove visibility check from `fill()` method in PlaywrightAdapter
2. ✅ Re-run test to validate steps 6-9 complete
3. ✅ Document multi-step form navigation requirement for production
4. 🔄 Plan Phase 14C: Form Navigation Support

---

## Status

**Phase 14B.1: Multi-Step Form Visibility - INVESTIGATING** 🔍

Current: 5/10 steps completing
Target: 10/10 steps completing
Blocker: Hidden form sections failing visibility checks


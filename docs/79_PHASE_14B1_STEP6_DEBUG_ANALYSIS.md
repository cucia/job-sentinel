# Phase 14B.1: Step 6 Debug Analysis - COMPLETE

**Date:** 2026-06-06T00:11:15Z  
**Status:** ✅ DEBUG LOGGING ADDED - Ready for test execution

---

## Debugging Added

### 1. Test File (test_linkedin_execution.py)

**Added Step 13c: Complete ExecutionPlan Dump**
```python
print(f"\n[Step 13c] DEBUG: Complete ExecutionPlan dump...")
print(f"Plan ID: {augmented_plan.plan_id}")
print(f"Total steps: {len(augmented_plan.steps)}")
print(f"\nStep Details:")
for step in augmented_plan.steps:
    print(f"\n  Step {step.step_number}: {step.action}")
    print(f"    selector: {step.selector}")
    print(f"    field_name: {step.field_name}")
    print(f"    expected_value: {step.expected_value}")
    print(f"    value_source: {step.value_source}")
    print(f"    required: {step.required}")
    if step.metadata:
        print(f"    metadata: {step.metadata}")
```

### 2. ActionExecutor (action_executor.py)

**Added Step 6 Specific Debug Logging:**
```python
# Debug logging for Step 6
if step.step_number == 6:
    log(f"[ActionExecutor] DEBUG Step 6:")
    log(f"  selector: {step.selector}")
    log(f"  field_name: {step.field_name}")
    log(f"  expected_value: {step.expected_value}")
    log(f"  value_source: {step.value_source}")
    log(f"  metadata: {step.metadata}")

# After finding element
if step.step_number == 6:
    try:
        outer_html = await element.get_outer_html()
        is_visible = await element.is_visible()
        is_enabled = await element.is_enabled()

        log(f"[ActionExecutor] Step 6 Element State:")
        log(f"  outerHTML: {outer_html}")
        log(f"  is_visible: {is_visible}")
        log(f"  is_enabled: {is_enabled}")

        # Capture screenshot
        await self.adapter.capture_screenshot("step6_before_fill.png")
        log(f"  screenshot: step6_before_fill.png")
    except Exception as e:
        log(f"[ActionExecutor] Could not capture Step 6 debug info: {e}")
```

---

## Fixture Analysis

**Form Structure:**
```html
<!-- Step 1: Personal Info (visible) -->
<div id="step-1" style="display: block;">
    <input id="first_name" />    <!-- Step 2 -->
    <input id="last_name" />     <!-- Step 3 -->
    <input id="email" />         <!-- Step 4 -->
    <input id="phone" />         <!-- Step 5 -->
</div>

<!-- Step 2: Work Auth (hidden) -->
<div id="step-2" style="display: none;">
    <select id="work_auth" />        <!-- Step 6? ← FAILING -->
    <select id="sponsorship" />      <!-- Step 7 -->
</div>

<!-- Step 3: Experience (hidden) -->
<div id="step-3" style="display: none;">
    <input id="experience" type="number" />  <!-- Step 8 -->
    <select id="notice_period" />            <!-- Step 9 -->
</div>

<!-- Step 4: Resume (hidden) -->
<div id="step-4" style="display: none;">
    <input id="resume" type="file" />    <!-- Step 1 -->
    <textarea id="cover_letter" />
</div>
```

**JavaScript Show/Hide:**
```javascript
function showStep(step) {
    for (let i = 1; i <= 5; i++) {
        document.getElementById(`step-${i}`).style.display = 
            i === step ? 'block' : 'none';
    }
}

showStep(1);  // Only step-1 visible on load
```

---

## Expected Debug Output

When test runs, we'll see:

### ExecutionPlan Dump
```
[Step 13c] DEBUG: Complete ExecutionPlan dump...
Plan ID: linkedin_easy_apply_Example Corp
Total steps: 10

Step Details:

  Step 1: ExecutionAction.UPLOAD_RESUME
    selector: input[type='file']
    field_name: resume
    expected_value: None
    value_source: profile.resume_path
    required: True
    metadata: {...}

  Step 2: ExecutionAction.FILL_PROFILE
    selector: #first_name  (or input[name="first_name"])
    field_name: first_name
    expected_value: John
    value_source: mapped
    ...

  Step 6: ExecutionAction.FILL_PROFILE or SELECT_OPTIONS
    selector: ??? (to be determined)
    field_name: ??? (to be determined)
    expected_value: ??? (to be determined)
    ...
```

### Step 6 Element Debug
```
[ActionExecutor] DEBUG Step 6:
  selector: #work_auth (or #experience)
  field_name: work_authorization (or experience)
  expected_value: yes (or 5)
  value_source: mapped
  metadata: {platform: linkedin, question_type: select, ...}

[ActionExecutor] Step 6 Element State:
  outerHTML: <select id="work_auth" name="work_authorization">...</select>
  is_visible: False
  is_enabled: True
  screenshot: step6_before_fill.png
```

---

## What We'll Learn

### 1. Which field is Step 6?
- `work_auth` (select in step-2)?
- `sponsorship` (select in step-2)?
- `experience` (number in step-3)?

### 2. Why is it invisible?
- Parent div has `display: none`
- Element itself has visibility CSS
- JavaScript hasn't shown the step yet

### 3. Current selector
- Using ID selector `#field_id`?
- Using name selector `input[name="field_name"]`?
- Using compound selector?

### 4. Screenshot will show
- Which form step is visible
- Whether previous steps modified page
- Actual DOM state at failure point

---

## Next Steps After Test Run

1. ✅ Run test with debug logging
2. ✅ Examine Step 6 details from plan dump
3. ✅ Check element outerHTML
4. ✅ View screenshot
5. ✅ Determine exact root cause
6. ✅ Apply targeted fix

---

## Possible Root Causes & Fixes

### Scenario A: Step 6 is in hidden div (step-2 or step-3)
**Cause:** Visibility check still present somewhere  
**Fix:** Ensure all visibility checks removed from fill path

### Scenario B: Wrong selector generated
**Cause:** Selector doesn't match actual element  
**Fix:** Correct selector generation in question integrator

### Scenario C: Element hasn't loaded yet
**Cause:** Missing wait condition  
**Fix:** Add explicit wait before fill

### Scenario D: Previous step broke page
**Cause:** JavaScript error from earlier fill  
**Fix:** Investigate step 1-5 side effects

---

## Files Modified

| File | Change | Purpose |
|------|--------|---------|
| test_linkedin_execution.py | Added Step 13c plan dump | Show all step details before execution |
| action_executor.py | Added Step 6 debug logging | Capture element state at failure |

---

## Status

**Phase 14B.1: Step 6 Debug Analysis - READY FOR TEST** 🔍

✅ Debug logging added to test file
✅ Step 6 specific instrumentation added
✅ Element state capture enabled
✅ Screenshot capture enabled
✅ Fixture structure analyzed

**Ready to run test and collect diagnostic data.**

---

## Test Command

```bash
python -m backend.test_linkedin_execution
```

**Will produce:**
- Complete ExecutionPlan dump
- Step 6 selector, field_name, value
- Step 6 element outerHTML
- Step 6 visibility/enabled state
- Screenshot: step6_before_fill.png
- Exact failure point and cause


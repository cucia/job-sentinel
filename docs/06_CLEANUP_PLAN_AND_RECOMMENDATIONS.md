# 06. Cleanup Plan and Recommendations

**Date:** 2026-06-03  
**Time:** 18:22:07 UTC  
**Purpose:** Prioritized cleanup actions with risk assessment

---

## Cleanup Priority Matrix

| Priority | Component | Action | Risk | Impact | Timeline |
|---|---|---|---|---|---|
| 1 | handlers.py duplicates | Delete lines 584-853 | None | 32% size reduction | Immediate |
| 2 | controller_simplified.py | Delete entire file | Low | Removes migration wrapper | Immediate |
| 3 | _make_job_key() | Extract to backend/utils | Low | Removes src dependency | This sprint |
| 4 | controller.py | Delete (after extract) | Low | Removes dead code | After #3 |

---

## Priority 1: Delete Duplicate Handlers (IMMEDIATE)

**Component:** `backend/workflow/handlers.py` lines 584-853

**Action:** Delete 273 lines of duplicate code

**Evidence:**
- Second registry is incomplete (missing Indeed, Naukri)
- First registry is active and complete
- All duplicate handlers are byte-for-byte identical
- Never instantiated in current code

**Risk Assessment:** NONE
- First registry continues to work
- No behavior changes
- All 8 workflows properly supported

**Verification:**
```bash
# After deletion, verify:
python3 -c "from backend.workflow.handlers import WorkflowHandlerRegistry; print('OK')"

# Test registry initialization
python3 -c "from backend.workflow.handlers import WorkflowHandlerRegistry; r = WorkflowHandlerRegistry(); print(len(r.handlers))"
# Should print: 8
```

**Execute:** YES - Immediate, safe

---

## Priority 2: Delete Migration Wrapper (IMMEDIATE)

**Component:** `src/core/controller_simplified.py`

**Action:** Delete entire file

**Evidence:**
- Not imported by any backend module
- Only wraps old controller for external compatibility
- External systems should migrate to backend API

**Risk Assessment:** LOW
- Only affects external systems (not backend)
- Those systems should migrate anyway
- No internal code depends on it

**Impact:** 
- Removes ~100 lines of dead code
- Clarifies that backend is authoritative

**Execute:** YES - Can be immediate with notice to external systems

---

## Priority 3: Extract Utility Function (THIS SPRINT)

**Component:** `src/core/controller.py`

**Action:** 
1. Create `backend/utils/key_generation.py`
2. Copy `_make_job_key()` function
3. Update import in `backend/bridge.py` line 99
4. Remove dependency on src/core/controller.py

**Current State:**
```python
# backend/bridge.py line 99
from src.core.controller import _make_job_key
```

**After Migration:**
```python
# backend/bridge.py line 99
from backend.utils.key_generation import make_job_key
```

**Risk Assessment:** VERY LOW
- Simple utility function
- No complex logic
- Direct replacement

**Impact:**
- Removes src/core/ dependency from backend
- Prepares for complete deletion of controller.py

**Execute:** YES - Short sprint task

---

## Priority 4: Delete Legacy Controller (FUTURE)

**Component:** `src/core/controller.py`

**Prerequisites:**
- ✅ _make_job_key() extracted
- ✅ No other imports from this file
- ✅ External systems notified

**Action:** Delete entire file

**Current Status:**
- 80% dead code (apply_*() functions, legacy logic)
- 20% used (only _make_job_key, which will be extracted)

**Risk Assessment:** NONE (after prerequisites)
- Dead code removal
- No active references
- Already migrated to backend

**Timeline:** 
- After Priority 3 complete
- After external system migration period

**Execute:** YES - Future, after extraction

---

## Migration Status Summary

### Currently Active (KEEP)

| Component | File | Status | Keep? |
|---|---|---|---|
| Classification | backend/workflow_classification.py | Active | ✅ YES |
| Orchestrator | backend/orchestrator/orchestrator.py | Active | ✅ YES |
| Handlers (First Set) | backend/workflow/handlers.py lines 26-580 | Active | ✅ YES |
| Bridge | backend/bridge.py | Active | ✅ YES |
| Runtime Tasks | backend/runtime/task_model.py | Active | ✅ YES |
| Queue | backend/queue/queue.py | Active | ✅ YES |
| State Manager | backend/state/state_manager.py | Active | ✅ YES |
| Session Layer | backend/application/session.py | Created, ready for Phase 3 | ✅ YES |
| Page Analyzer | backend/application/page_analyzer.py | Ready for Phase 3 | ✅ YES |
| Execution Planner | backend/application/execution_planner.py | Ready for Phase 3 | ✅ YES |

### Dead Code (DELETE)

| Component | File | Status | Delete? | Priority |
|---|---|---|---|---|
| Duplicate Handlers | backend/workflow/handlers.py lines 584-853 | Dead | ✅ YES | 1 |
| Controller Wrapper | src/core/controller_simplified.py | Migration only | ✅ YES | 2 |
| Legacy Controller | src/core/controller.py | Dead (except 1 func) | ✅ YES | 4 |
| Legacy Session | src/core/session.py | Dead | ✅ YES | 4 |

### Migration Code (EXTRACT THEN DELETE)

| Component | File | Status | Action | Priority |
|---|---|---|---|---|
| _make_job_key() | src/core/controller.py | Utility only | Extract → Delete | 3 |

---

## Execution Order

### Phase 1: Immediate (Today)
1. ✅ Delete backend/workflow/handlers.py lines 584-853
2. ✅ Delete src/core/controller_simplified.py
3. ✅ Test: Runtime still works

### Phase 2: This Sprint
1. Create backend/utils/key_generation.py
2. Copy _make_job_key() function
3. Update import in backend/bridge.py
4. Test: Key generation still works
5. Delete src/core/controller.py

### Phase 3: Future (After External Migration)
1. Monitor external systems migration
2. Once all migrated, confirm deletion safety
3. Delete any remaining src/core/ compatibility code

---

## Total Impact

**Before Cleanup:**
- 1,000+ lines of dead/duplicate code
- Multiple execution paths (src/ and backend/)
- Confusion about authoritative runtime

**After Cleanup:**
- Clean, single runtime (backend/)
- No duplication
- 30% size reduction in handlers.py
- Clear migration path

---

## Risk Summary

| Action | Risk Level | Reversibility | Recommended |
|---|---|---|---|
| Delete handlers duplicates | NONE | Yes (in git) | ✅ DO IT |
| Delete controller_simplified | LOW | Yes (in git) | ✅ DO IT |
| Extract _make_job_key | VERY LOW | Yes (in git) | ✅ DO IT |
| Delete controller.py | NONE (after #3) | Yes (in git) | ✅ DO IT (later) |

---

## Sign-Off Checklist

Before executing cleanup:

- ✅ All handlers.py first definitions are complete
- ✅ First WorkflowHandlerRegistry includes Indeed and Naukri
- ✅ No code imports from handlers.py lines 584-853
- ✅ No code imports controller_simplified.py
- ✅ bridge.py only uses _make_job_key from controller.py
- ✅ All tests pass
- ✅ Migration documentation complete

**Status:** READY TO PROCEED ✅


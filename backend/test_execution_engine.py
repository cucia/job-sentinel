"""
Execution Engine Validation Tests

Tests the ExecutionEngine foundation phase:
- Plan validation
- Step execution simulation
- State tracking
- Session history updates
- Failure handling
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.execution.engine import ExecutionEngine
from backend.execution.result import ExecutionResult
from backend.execution.state_tracker import StateTracker
from backend.application.session import ApplicationSession
from backend.application.execution_planner import ExecutionPlan, ExecutionPlanStep, ExecutionAction


def test_empty_plan():
    """Test 1: Empty plan handling."""
    print("\n=== Test 1: Empty Plan ===\n")

    try:
        engine = ExecutionEngine()
        session = ApplicationSession(
            session_id="session_1",
            job_id="job_1",
            task_id="task_1",
            workflow_type="linkedin_easy_apply",
            current_url="https://example.com",
        )

        plan = ExecutionPlan(
            plan_id="plan_empty",
            workflow_type="linkedin_easy_apply",
            job_id="job_1",
            task_id="task_1",
            steps=[],
            total_estimated_duration=0,
            confidence_score=1.0,
        )

        print("✓ Executing empty plan")
        result = engine.execute(session, plan, dry_run=True)

        print(f"  - success: {result.success}")
        print(f"  - completed_steps: {result.completed_steps}")
        print(f"  - status: {result.status}")

        assert result.success == True
        assert result.completed_steps == 0
        assert result.status == "completed"

        print("✅ Empty plan handled correctly")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_step_plan():
    """Test 2: Single-step plan execution."""
    print("\n=== Test 2: Single-Step Plan ===\n")

    try:
        engine = ExecutionEngine()
        session = ApplicationSession(
            session_id="session_2",
            job_id="job_2",
            task_id="task_2",
            workflow_type="linkedin_easy_apply",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=1,
            action=ExecutionAction.FILL_PROFILE,
            description="Fill profile information",
            estimated_duration_seconds=60,
            validation_checks=["required_fields_filled"],
        )

        plan = ExecutionPlan(
            plan_id="plan_single",
            workflow_type="linkedin_easy_apply",
            job_id="job_2",
            task_id="task_2",
            steps=[step],
            total_estimated_duration=60,
            confidence_score=0.95,
        )

        print("✓ Executing single-step plan")
        result = engine.execute(session, plan, dry_run=True)

        print(f"  - success: {result.success}")
        print(f"  - completed_steps: {result.completed_steps}")
        print(f"  - status: {result.status}")
        print(f"  - execution_time: {result.execution_time:.2f}s")

        assert result.success == True
        assert result.completed_steps == 1
        assert result.status == "completed"
        assert len(session.execution_history) > 0

        print("✅ Single-step plan executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_step_plan():
    """Test 3: Multi-step plan execution."""
    print("\n=== Test 3: Multi-Step Plan ===\n")

    try:
        engine = ExecutionEngine()
        session = ApplicationSession(
            session_id="session_3",
            job_id="job_3",
            task_id="task_3",
            workflow_type="indeed",
            current_url="https://example.com",
        )

        steps = [
            ExecutionPlanStep(
                step_number=1,
                action=ExecutionAction.UPLOAD_RESUME,
                description="Upload resume",
                estimated_duration_seconds=30,
                validation_checks=["file_uploaded"],
            ),
            ExecutionPlanStep(
                step_number=2,
                action=ExecutionAction.FILL_PROFILE,
                description="Fill profile",
                estimated_duration_seconds=60,
                validation_checks=["fields_filled"],
            ),
            ExecutionPlanStep(
                step_number=3,
                action=ExecutionAction.SUBMIT_APPLICATION,
                description="Submit application",
                estimated_duration_seconds=10,
                validation_checks=["submission_successful"],
            ),
        ]

        plan = ExecutionPlan(
            plan_id="plan_multi",
            workflow_type="indeed",
            job_id="job_3",
            task_id="task_3",
            steps=steps,
            total_estimated_duration=100,
            confidence_score=0.88,
        )

        print("✓ Executing multi-step plan (3 steps)")
        result = engine.execute(session, plan, dry_run=True)

        print(f"  - success: {result.success}")
        print(f"  - completed_steps: {result.completed_steps}")
        print(f"  - status: {result.status}")
        print(f"  - execution_time: {result.execution_time:.2f}s")

        assert result.success == True
        assert result.completed_steps == 3
        assert result.status == "completed"

        print("✅ Multi-step plan executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plan_validation():
    """Test 4: Plan validation."""
    print("\n=== Test 4: Plan Validation ===\n")

    try:
        engine = ExecutionEngine()
        session = ApplicationSession(
            session_id="session_4",
            job_id="job_4",
            task_id="task_4",
            workflow_type="naukri",
            current_url="https://example.com",
        )

        # Create step with invalid numbering
        step = ExecutionPlanStep(
            step_number=2,  # Should be 1
            action=ExecutionAction.FILL_PROFILE,
            description="Fill profile",
            estimated_duration_seconds=60,
        )

        plan = ExecutionPlan(
            plan_id="plan_invalid",
            workflow_type="naukri",
            job_id="job_4",
            task_id="task_4",
            steps=[step],
            total_estimated_duration=60,
            confidence_score=0.80,
        )

        print("✓ Executing plan with invalid step numbering")
        result = engine.execute(session, plan, dry_run=True)

        print(f"  - success: {result.success}")
        print(f"  - status: {result.status}")
        print(f"  - errors: {result.errors}")

        assert result.success == False
        assert result.status == "failed"

        print("✅ Plan validation correctly rejected invalid plan")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_tracking():
    """Test 5: State tracking during execution."""
    print("\n=== Test 5: State Tracking ===\n")

    try:
        tracker = StateTracker("plan_1", 3)

        print("✓ Starting execution")
        tracker.start_execution()
        assert tracker.status == "in_progress"

        print("✓ Completing step 1")
        tracker.complete_step(1, "Step 1", 10.0)
        assert 1 in tracker.completed_steps
        assert tracker.current_step == 1

        print("✓ Completing step 2")
        tracker.complete_step(2, "Step 2", 20.0)
        assert 2 in tracker.completed_steps

        print("✓ Completing step 3")
        tracker.complete_step(3, "Step 3", 30.0)
        assert 3 in tracker.completed_steps

        print("✓ Finishing execution")
        tracker.finish_execution(True)
        assert tracker.status == "completed"

        state = tracker.get_state()
        print(f"  - total_steps: {state['total_steps']}")
        print(f"  - completed_steps: {len(state['completed_steps'])}")
        print(f"  - execution_time: {state['execution_time']:.2f}s")

        assert len(state["completed_steps"]) == 3
        assert state["execution_time"] > 0

        print("✅ State tracking working correctly")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_session_history_update():
    """Test 6: Session history updates."""
    print("\n=== Test 6: Session History Updates ===\n")

    try:
        engine = ExecutionEngine()
        session = ApplicationSession(
            session_id="session_6",
            job_id="job_6",
            task_id="task_6",
            workflow_type="linkedin_easy_apply",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=1,
            action=ExecutionAction.FILL_PROFILE,
            description="Fill profile",
            estimated_duration_seconds=60,
        )

        plan = ExecutionPlan(
            plan_id="plan_session",
            workflow_type="linkedin_easy_apply",
            job_id="job_6",
            task_id="task_6",
            steps=[step],
            total_estimated_duration=60,
            confidence_score=0.95,
        )

        print("✓ Initial execution history:", len(session.execution_history))
        assert len(session.execution_history) == 0

        print("✓ Executing plan")
        result = engine.execute(session, plan, dry_run=True)

        print(f"  - execution_history entries: {len(session.execution_history)}")
        assert len(session.execution_history) > 0

        history = session.execution_history[0]
        print(f"  - completed_steps: {len(history['completed_steps'])}")
        print(f"  - status: {history['status']}")

        assert history["completed_steps"] == [1]
        assert history["status"] == "completed"

        print("✅ Session history updated correctly")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("EXECUTION ENGINE FOUNDATION VALIDATION")
    print("="*70)

    results = {}

    results["empty_plan"] = test_empty_plan()
    results["single_step_plan"] = test_single_step_plan()
    results["multi_step_plan"] = test_multi_step_plan()
    results["plan_validation"] = test_plan_validation()
    results["state_tracking"] = test_state_tracking()
    results["session_history_update"] = test_session_history_update()

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*70)
        print("✅ EXECUTION ENGINE FOUNDATION COMPLETE")
        print("="*70)
        print("\nCapabilities validated:")
        print("  ✅ Empty plan handling")
        print("  ✅ Single-step execution")
        print("  ✅ Multi-step execution")
        print("  ✅ Plan validation")
        print("  ✅ State tracking")
        print("  ✅ Session history updates")
        print("\nReady for:")
        print("  • Browser automation integration (Phase 5+)")
        print("  • Playwright connection")
        print("  • Real DOM interaction")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

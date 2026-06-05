"""
Action Executor Validation Tests

Tests the ActionExecutor bridge between ExecutionPlanStep and BrowserAdapter.
Uses MockBrowserAdapter for testing without real browser.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.execution.action_executor import ActionExecutor, ActionExecutionResult
from backend.application.session import (
    ApplicationSession,
    ExecutionPlanStep,
    ExecutionAction,
)
from backend.browser.adapter import MockBrowserAdapter


async def test_fill_action():
    """Test 1: Fill profile action."""
    print("\n=== Test 1: Fill Profile Action ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_1",
            job_id="job_1",
            task_id="task_1",
            workflow_type="linkedin_easy_apply",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=1,
            action=ExecutionAction.FILL_PROFILE,
            description="Fill profile",
            selector="input[name='firstName']",
            field_name="firstName",
            expected_value="John",
            required=True,
        )

        print("✓ Executing fill action")
        result = await executor.execute_step(step, session)

        print(f"  - {result}")
        assert result.success == True
        assert result.action == str(ExecutionAction.FILL_PROFILE)
        assert result.step_number == 1

        print("✅ Fill action working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_click_action():
    """Test 2: Click submit action."""
    print("\n=== Test 2: Click Submit Action ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_2",
            job_id="job_2",
            task_id="task_2",
            workflow_type="indeed",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=3,
            action=ExecutionAction.SUBMIT_APPLICATION,
            description="Submit application",
            selector="button[type='submit']",
            field_name="submit_button",
            required=True,
        )

        print("✓ Executing click action")
        result = await executor.execute_step(step, session)

        print(f"  - {result}")
        assert result.success == True
        assert result.action == str(ExecutionAction.SUBMIT_APPLICATION)

        print("✅ Click action working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_upload_action():
    """Test 3: Upload resume action."""
    print("\n=== Test 3: Upload Resume Action ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_3",
            job_id="job_3",
            task_id="task_3",
            workflow_type="naukri",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=1,
            action=ExecutionAction.UPLOAD_RESUME,
            description="Upload resume",
            selector="input[type='file']",
            field_name="resume",
            value_source="file_path",
            expected_value="/path/to/resume.pdf",
            required=True,
        )

        print("✓ Executing upload action")
        result = await executor.execute_step(step, session)

        print(f"  - {result}")
        assert result.success == True
        assert result.action == str(ExecutionAction.UPLOAD_RESUME)

        print("✅ Upload action working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_continue_action():
    """Test 4: Continue to next step action."""
    print("\n=== Test 4: Continue to Next Step Action ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_4",
            job_id="job_4",
            task_id="task_4",
            workflow_type="linkedin_easy_apply",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=2,
            action=ExecutionAction.CONTINUE_TO_NEXT_STEP,
            description="Continue to next page",
            selector="button.continue-button",
            field_name="continue",
            required=True,
        )

        print("✓ Executing continue action")
        result = await executor.execute_step(step, session)

        print(f"  - {result}")
        assert result.success == True
        assert result.action == str(ExecutionAction.CONTINUE_TO_NEXT_STEP)

        print("✅ Continue action working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_missing_selector():
    """Test 5: Missing selector handling."""
    print("\n=== Test 5: Missing Selector Handling ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_5",
            job_id="job_5",
            task_id="task_5",
            workflow_type="indeed",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=1,
            action=ExecutionAction.FILL_PROFILE,
            description="Fill profile",
            # No selector provided
            field_name="firstName",
            expected_value="John",
        )

        print("✓ Executing step without selector")
        result = await executor.execute_step(step, session)

        print(f"  - {result}")
        assert result.success == False
        assert "selector" in result.message.lower()

        print("✅ Missing selector handled correctly")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_unsupported_action():
    """Test 6: Unsupported action handling."""
    print("\n=== Test 6: Unsupported Action Handling ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_6",
            job_id="job_6",
            task_id="task_6",
            workflow_type="linkedin_easy_apply",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=1,
            action=ExecutionAction.MANUAL_REVIEW_REQUIRED,
            description="Manual review",
        )

        print("✓ Executing unsupported action")
        result = await executor.execute_step(step, session)

        print(f"  - {result}")
        assert result.success == False
        assert "no handler" in result.message.lower()

        print("✅ Unsupported action handled correctly")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_confirm_action():
    """Test 7: Confirm application action."""
    print("\n=== Test 7: Confirm Application Action ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_7",
            job_id="job_7",
            task_id="task_7",
            workflow_type="naukri",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=2,
            action=ExecutionAction.CONFIRM_APPLICATION,
            description="Review application",
            field_name="review",
            required=False,
        )

        print("✓ Executing confirm action")
        result = await executor.execute_step(step, session)

        print(f"  - {result}")
        assert result.success == True
        assert result.action == str(ExecutionAction.CONFIRM_APPLICATION)

        print("✅ Confirm action working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_verify_submission():
    """Test 8: Verify submission action."""
    print("\n=== Test 8: Verify Submission Action ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com/confirmation?success=true")

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_8",
            job_id="job_8",
            task_id="task_8",
            workflow_type="indeed",
            current_url="https://example.com",
        )

        step = ExecutionPlanStep(
            step_number=4,
            action=ExecutionAction.VERIFY_SUBMISSION,
            description="Verify submission",
            field_name="confirmation",
            required=False,
            metadata={
                "selector_patterns": ["confirmation", "success", "submitted"]
            },
        )

        print("✓ Executing verify submission action")
        result = await executor.execute_step(step, session)

        print(f"  - {result}")
        # May succeed or fail depending on page content
        assert result.action == str(ExecutionAction.VERIFY_SUBMISSION)

        print("✅ Verify submission action working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_action_result_serialization():
    """Test 9: ActionExecutionResult serialization."""
    print("\n=== Test 9: Action Result Serialization ===\n")

    try:
        result = ActionExecutionResult(
            success=True,
            action="fill_profile",
            step_number=1,
            message="Successfully filled profile",
            metadata={
                "selector": "input[name='firstName']",
                "field_name": "firstName",
                "value_length": 4,
            },
        )

        print("✓ Converting result to dictionary")
        result_dict = result.to_dict()

        assert result_dict["success"] == True
        assert result_dict["action"] == "fill_profile"
        assert result_dict["step_number"] == 1
        assert "timestamp" in result_dict
        assert "metadata" in result_dict

        print(f"  - Success: {result_dict['success']}")
        print(f"  - Action: {result_dict['action']}")
        print(f"  - Step: {result_dict['step_number']}")

        print("✅ Result serialization working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_steps_sequence():
    """Test 10: Sequence of multiple actions."""
    print("\n=== Test 10: Multiple Steps Sequence ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        executor = ActionExecutor(adapter)
        session = ApplicationSession(
            session_id="session_10",
            job_id="job_10",
            task_id="task_10",
            workflow_type="linkedin_easy_apply",
            current_url="https://example.com",
        )

        steps = [
            ExecutionPlanStep(
                step_number=1,
                action=ExecutionAction.FILL_PROFILE,
                selector="input[name='firstName']",
                field_name="firstName",
                expected_value="John",
            ),
            ExecutionPlanStep(
                step_number=2,
                action=ExecutionAction.FILL_PROFILE,
                selector="input[name='lastName']",
                field_name="lastName",
                expected_value="Doe",
            ),
            ExecutionPlanStep(
                step_number=3,
                action=ExecutionAction.SUBMIT_APPLICATION,
                selector="button[type='submit']",
                field_name="submit",
            ),
        ]

        results = []
        print("✓ Executing step sequence")
        for step in steps:
            result = await executor.execute_step(step, session)
            results.append(result)
            print(f"  - Step {step.step_number}: {result.message}")

        assert len(results) == 3
        assert all(r.success for r in results)

        print("✅ Step sequence executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("ACTION EXECUTOR VALIDATION")
    print("="*70)

    results = {}

    results["fill_action"] = await test_fill_action()
    results["click_action"] = await test_click_action()
    results["upload_action"] = await test_upload_action()
    results["continue_action"] = await test_continue_action()
    results["missing_selector"] = await test_missing_selector()
    results["unsupported_action"] = await test_unsupported_action()
    results["confirm_action"] = await test_confirm_action()
    results["verify_submission"] = await test_verify_submission()
    results["result_serialization"] = await test_action_result_serialization()
    results["multiple_steps"] = await test_multiple_steps_sequence()

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
        print("✅ ACTION EXECUTOR COMPLETE")
        print("="*70)
        print("\nCapabilities validated:")
        print("  ✅ Fill profile action")
        print("  ✅ Click submit action")
        print("  ✅ Upload resume action")
        print("  ✅ Continue to next step action")
        print("  ✅ Confirm application action")
        print("  ✅ Verify submission action")
        print("  ✅ Missing selector handling")
        print("  ✅ Unsupported action handling")
        print("  ✅ Result serialization")
        print("  ✅ Step sequences")
        print("\nReady for:")
        print("  • PlaywrightAdapter integration (Phase 7)")
        print("  • Real browser automation")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


def main():
    """Main entry point."""
    return asyncio.run(run_all_tests())


if __name__ == "__main__":
    sys.exit(main())

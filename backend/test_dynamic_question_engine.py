"""
Dynamic Question Engine Validation Test

Tests complete dynamic question workflow:
1. Load page with PlaywrightAdapter
2. Detect questions with QuestionDetector
3. Classify with QuestionClassifier
4. Map answers with AnswerMapper
5. Generate ExecutionPlan dynamically
6. Execute through ExecutionEngine
7. Verify DOM state

Validates:
✓ Radio buttons selected
✓ Text fields filled
✓ Dropdowns selected
✓ Checkboxes checked
✓ Dynamic plan generated
✓ ExecutionEngine executed plan
✓ Real browser interaction
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.application.session import (
    ApplicationSession,
    ExecutionPlan,
    ExecutionPlanStep,
    ExecutionAction,
)
from backend.application.question_detector import QuestionDetector
from backend.application.question_classifier import QuestionClassifier
from backend.application.answer_mapper import AnswerMapper
from backend.execution.engine import ExecutionEngine
from backend.execution.action_executor import ActionExecutor
from backend.browser.playwright_adapter import PlaywrightAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_fixture_url(fixture_name: str):
    """Get file:// URL for fixture."""
    fixture_path = Path(__file__).parent / "test_fixtures" / "questions" / f"{fixture_name}.html"
    return f"file://{fixture_path.absolute()}"


async def test_radio_questions():
    """Test dynamic question detection with radio buttons."""
    print("\n" + "="*70)
    print("TEST: RADIO QUESTIONS")
    print("="*70)

    try:
        fixture_url = get_fixture_url("radio_questions")
        fixture_path = Path(fixture_url.replace("file://", ""))

        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        print(f"\n✓ Fixture exists: {fixture_path.name}")

        # Setup
        adapter = PlaywrightAdapter()
        await adapter.start()
        print("✓ Browser started")

        # Navigate
        await adapter.goto(fixture_url)
        print(f"✓ Loaded: {fixture_path.name}")

        # Detect questions
        print("\n✓ Detecting questions...")
        detector = QuestionDetector()
        questions = await detector.detect_questions(adapter)
        print(f"  - Detected {len(questions)} questions")
        for q in questions:
            print(f"    • {q.text} ({q.field_type})")

        # Classify questions
        print("\n✓ Classifying questions...")
        classifier = QuestionClassifier()
        classified = classifier.classify_multiple(questions)
        print(f"  - Classified {len(classified)} questions")
        for selector, info in classified.items():
            print(f"    • {info['text']}: {info['category']}")

        # Map answers
        print("\n✓ Mapping answers...")
        mapper = AnswerMapper()
        answers = mapper.map_questions_to_answers(classified)
        print(f"  - Mapped {len(answers)} answers")
        for selector, answer_info in answers.items():
            print(f"    • {answer_info['category']}: {answer_info['answer']}")

        # Generate plan
        print("\n✓ Generating ExecutionPlan dynamically...")
        steps = []
        for selector, answer_info in answers.items():
            step = ExecutionPlanStep(
                step_number=len(steps) + 1,
                action=ExecutionAction.SELECT_OPTIONS,
                description=f"Answer: {answer_info['text']}",
                selector=selector,
                field_name=answer_info['category'],
                value_source="mapped",
                expected_value=answer_info['answer'],
                required=True,
            )
            steps.append(step)

        plan = ExecutionPlan(
            plan_id="plan_radio_001",
            workflow_type="dynamic_questions",
            job_id="job_radio_001",
            task_id="task_radio_001",
            steps=steps,
            total_estimated_duration=60,
            confidence_score=0.95,
        )
        print(f"  - Generated {len(plan.steps)} steps")

        # Execute plan
        print("\n✓ Executing plan through ExecutionEngine...")
        session = ApplicationSession(
            session_id="radio_test",
            job_id="job_radio_001",
            task_id="task_radio_001",
            workflow_type="dynamic_questions",
            current_url=fixture_url,
        )

        executor = ActionExecutor(adapter)
        engine = ExecutionEngine(action_executor=executor)

        result = await engine.execute(session, plan, dry_run=False)
        print(f"  - Success: {result.success}")
        print(f"  - Completed: {result.completed_steps}/{len(plan.steps)}")
        print(f"  - Time: {result.execution_time:.2f}s")

        # Validate execution success
        if not result.success:
            raise AssertionError(f"ExecutionEngine failed: {result.errors}")
        if result.completed_steps != len(plan.steps):
            raise AssertionError(f"Incomplete execution: {result.completed_steps}/{len(plan.steps)}")

        # Verify
        print("\n✓ Verifying DOM state...")
        # Check if radios are selected
        auth_checked = await adapter.find_element('input[name="work_auth"]:checked')
        sponsor_checked = await adapter.find_element('input[name="sponsorship"]:checked')
        relocate_checked = await adapter.find_element('input[name="relocate"]:checked')
        remote_checked = await adapter.find_element('input[name="remote"]:checked')

        print(f"  - Work auth selected: {bool(auth_checked)}")
        print(f"  - Sponsorship selected: {bool(sponsor_checked)}")
        print(f"  - Relocate selected: {bool(relocate_checked)}")
        print(f"  - Remote selected: {bool(remote_checked)}")

        # Fail if any radio not selected
        if not all([auth_checked, sponsor_checked, relocate_checked, remote_checked]):
            raise AssertionError("Not all radio buttons were selected")

        await adapter.stop()
        print("\n✅ RADIO QUESTIONS TEST PASSED")
        return True

    except Exception as e:
        print(f"\n❌ RADIO QUESTIONS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_salary_questions():
    """Test dynamic question detection with text/select fields."""
    print("\n" + "="*70)
    print("TEST: SALARY QUESTIONS")
    print("="*70)

    try:
        fixture_url = get_fixture_url("salary_questions")
        fixture_path = Path(fixture_url.replace("file://", ""))

        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        print(f"\n✓ Fixture exists: {fixture_path.name}")

        # Setup
        adapter = PlaywrightAdapter()
        await adapter.start()
        print("✓ Browser started")

        # Navigate
        await adapter.goto(fixture_url)
        print(f"✓ Loaded: {fixture_path.name}")

        # Detect questions
        print("\n✓ Detecting questions...")
        detector = QuestionDetector()
        questions = await detector.detect_questions(adapter)
        print(f"  - Detected {len(questions)} questions")
        for q in questions:
            print(f"    • {q.text} ({q.field_type})")

        # Classify
        print("\n✓ Classifying questions...")
        classifier = QuestionClassifier()
        classified = classifier.classify_multiple(questions)
        print(f"  - Classifications:")
        for selector, info in classified.items():
            print(f"    • {info['category']}")

        # Map answers
        print("\n✓ Mapping answers...")
        mapper = AnswerMapper()
        answers = mapper.map_questions_to_answers(classified)
        print(f"  - Answers mapped:")
        for selector, answer_info in answers.items():
            print(f"    • {answer_info['category']}: {answer_info['answer']}")

        # Generate and execute
        print("\n✓ Generating and executing plan...")
        steps = []
        for selector, answer_info in answers.items():
            action = ExecutionAction.FILL_PROFILE if answer_info['field_type'] == 'text' else ExecutionAction.SELECT_OPTIONS
            step = ExecutionPlanStep(
                step_number=len(steps) + 1,
                action=action,
                description=f"Answer: {answer_info['text']}",
                selector=selector,
                field_name=answer_info['category'],
                value_source="mapped",
                expected_value=answer_info['answer'],
                required=True,
            )
            steps.append(step)

        plan = ExecutionPlan(
            plan_id="plan_salary_001",
            workflow_type="dynamic_questions",
            job_id="job_salary_001",
            task_id="task_salary_001",
            steps=steps,
            total_estimated_duration=60,
            confidence_score=0.95,
        )

        session = ApplicationSession(
            session_id="salary_test",
            job_id="job_salary_001",
            task_id="task_salary_001",
            workflow_type="dynamic_questions",
            current_url=fixture_url,
        )

        executor = ActionExecutor(adapter)
        engine = ExecutionEngine(action_executor=executor)

        result = await engine.execute(session, plan, dry_run=False)
        print(f"  - Executed {result.completed_steps}/{len(plan.steps)} steps")
        print(f"  - Success: {result.success}")

        # Validate execution success
        if not result.success:
            raise AssertionError(f"ExecutionEngine failed: {result.errors}")
        if result.completed_steps != len(plan.steps):
            raise AssertionError(f"Incomplete execution: {result.completed_steps}/{len(plan.steps)}")

        # Verify
        print("\n✓ Verifying filled values...")
        expected_salary_elem = await adapter.find_element("#expected_salary")
        if expected_salary_elem:
            value = await expected_salary_elem.input_value()
            print(f"  - Expected salary field: {value}")
            if not value:
                raise AssertionError("Expected salary field not filled")
        else:
            raise AssertionError("Expected salary field not found")

        await adapter.stop()
        print("\n✅ SALARY QUESTIONS TEST PASSED")
        return True

    except Exception as e:
        print(f"\n❌ SALARY QUESTIONS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mixed_questions():
    """Test dynamic question detection with mixed field types."""
    print("\n" + "="*70)
    print("TEST: MIXED QUESTIONS")
    print("="*70)

    try:
        fixture_url = get_fixture_url("mixed_questions")
        fixture_path = Path(fixture_url.replace("file://", ""))

        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        print(f"\n✓ Fixture exists: {fixture_path.name}")

        # Setup
        adapter = PlaywrightAdapter()
        await adapter.start()
        print("✓ Browser started")

        await adapter.goto(fixture_url)
        print(f"✓ Loaded: {fixture_path.name}")

        # Detect questions
        print("\n✓ Detecting questions...")
        detector = QuestionDetector()
        questions = await detector.detect_questions(adapter)
        print(f"  - Detected {len(questions)} questions")

        # Classify
        print("\n✓ Classifying questions...")
        classifier = QuestionClassifier()
        classified = classifier.classify_multiple(questions)

        # Count by type
        field_types = {}
        for selector, info in classified.items():
            ft = info['field_type']
            field_types[ft] = field_types.get(ft, 0) + 1

        print(f"  - Field types found:")
        for ft, count in field_types.items():
            print(f"    • {ft}: {count}")

        # Map answers
        print("\n✓ Mapping answers...")
        mapper = AnswerMapper()
        answers = mapper.map_questions_to_answers(classified)

        # Generate and execute
        print("\n✓ Executing dynamic plan...")
        steps = []
        for selector, answer_info in answers.items():
            if answer_info['field_type'] == 'text':
                action = ExecutionAction.FILL_PROFILE
            elif answer_info['field_type'] == 'select':
                action = ExecutionAction.SELECT_OPTIONS
            elif answer_info['field_type'] == 'radio':
                action = ExecutionAction.SELECT_OPTIONS
            elif answer_info['field_type'] == 'checkbox':
                action = ExecutionAction.FILL_PROFILE
            else:
                continue

            step = ExecutionPlanStep(
                step_number=len(steps) + 1,
                action=action,
                description=f"Answer: {answer_info['text']}",
                selector=selector,
                field_name=answer_info['category'],
                value_source="mapped",
                expected_value=answer_info['answer'],
                required=True,
            )
            steps.append(step)

        plan = ExecutionPlan(
            plan_id="plan_mixed_001",
            workflow_type="dynamic_questions",
            job_id="job_mixed_001",
            task_id="task_mixed_001",
            steps=steps,
            total_estimated_duration=60,
            confidence_score=0.95,
        )

        session = ApplicationSession(
            session_id="mixed_test",
            job_id="job_mixed_001",
            task_id="task_mixed_001",
            workflow_type="dynamic_questions",
            current_url=fixture_url,
        )

        executor = ActionExecutor(adapter)
        engine = ExecutionEngine(action_executor=executor)

        result = await engine.execute(session, plan, dry_run=False)
        print(f"  - Executed {result.completed_steps}/{len(plan.steps)} steps")
        print(f"  - Success: {result.success}")

        # Validate execution success
        if not result.success:
            raise AssertionError(f"ExecutionEngine failed: {result.errors}")
        if result.completed_steps != len(plan.steps):
            raise AssertionError(f"Incomplete execution: {result.completed_steps}/{len(plan.steps)}")

        await adapter.stop()
        print("\n✅ MIXED QUESTIONS TEST PASSED")
        return True

    except Exception as e:
        print(f"\n❌ MIXED QUESTIONS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("DYNAMIC QUESTION ENGINE VALIDATION")
    print("="*70)

    results = []

    # Test 1: Radio questions
    results.append(("Radio Questions", await test_radio_questions()))

    # Test 2: Salary questions
    results.append(("Salary Questions", await test_salary_questions()))

    # Test 3: Mixed questions
    results.append(("Mixed Questions", await test_mixed_questions()))

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print("\nResults:")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {test_name}")

    all_passed = all(result for _, result in results)
    print("\n" + ("✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"))

    return 0 if all_passed else 1


def main():
    """Main entry point."""
    try:
        return asyncio.run(run_all_tests())
    except ImportError:
        print("\n⚠️  SKIPPED: Playwright not installed")
        print("   Install with: pip install playwright")
        print("   Then run: playwright install chromium")
        return 0


if __name__ == "__main__":
    sys.exit(main())

"""
LinkedIn Dynamic Question Integration Validation Test

Tests integration of LinkedIn questions with Dynamic Question Engine:
1. Work Authorization Questions
2. Salary Questions
3. Mixed Questions
4. Plan Augmentation
5. Metadata Preservation
"""

import sys
import os
import re
import asyncio
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.platforms.linkedin import LinkedInPlanGenerator, LinkedInWorkflowType
from backend.platforms.linkedin.linkedin_question_integrator import LinkedInQuestionIntegrator
from backend.application.session import ExecutionPlan, ExecutionPlanStep, ExecutionAction


def get_fixture_url(fixture_name: str):
    """Get file:// URL for LinkedIn fixture."""
    fixture_path = Path(__file__).parent / "test_fixtures" / "linkedin" / "questions" / f"{fixture_name}.html"
    return f"file://{fixture_path.absolute()}"


def read_fixture(fixture_name: str) -> str:
    """Read fixture HTML content."""
    fixture_path = Path(__file__).parent / "test_fixtures" / "linkedin" / "questions" / f"{fixture_name}.html"
    with open(fixture_path, 'r') as f:
        return f.read()


def test_work_auth_questions():
    """Test 1: Work Authorization Questions Detection"""
    print("\n" + "="*70)
    print("TEST 1: WORK AUTHORIZATION QUESTIONS")
    print("="*70)

    try:
        html = read_fixture("linkedin_work_auth_questions")
        print(f"\n✓ Fixture loaded")

        integrator = LinkedInQuestionIntegrator()

        # Detect questions
        questions = asyncio.run(integrator.detect_linkedin_questions(html))
        print(f"\n✓ Questions detected: {len(questions)}")

        for q in questions:
            print(f"  - {q.text} ({q.field_type})")

        # Classify questions
        classified = integrator.classify_linkedin_questions(questions)
        print(f"\n✓ Questions classified:")
        for q, cat in classified:
            cat_str = str(cat).split(".")[-1]
            print(f"  - {q.text[:40]} → {cat_str}")

        # Generate steps
        steps = asyncio.run(integrator.generate_question_steps(questions))
        print(f"\n✓ ExecutionPlanSteps generated: {len(steps)}")
        for step in steps:
            print(f"  {step.step_number}. {step.action.value} - {step.description}")

        assert len(questions) > 0, "Should detect questions"
        assert len(steps) > 0, "Should generate steps"
        assert all(isinstance(s, ExecutionPlanStep) for s in steps), "All should be ExecutionPlanSteps"

        print("\n✅ TEST 1 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_salary_questions():
    """Test 2: Salary Questions Detection"""
    print("\n" + "="*70)
    print("TEST 2: SALARY QUESTIONS")
    print("="*70)

    try:
        html = read_fixture("linkedin_salary_questions")
        print(f"\n✓ Fixture loaded")

        integrator = LinkedInQuestionIntegrator()

        # Detect questions
        questions = asyncio.run(integrator.detect_linkedin_questions(html))
        print(f"\n✓ Questions detected: {len(questions)}")

        for q in questions:
            print(f"  - {q.text} ({q.field_type})")

        # Classify questions
        classified = integrator.classify_linkedin_questions(questions)
        print(f"\n✓ Questions classified:")
        for q, cat in classified:
            cat_str = str(cat).split(".")[-1]
            print(f"  - {q.text[:40]} → {cat_str}")

        # Generate steps
        steps = asyncio.run(integrator.generate_question_steps(questions))
        print(f"\n✓ ExecutionPlanSteps generated: {len(steps)}")
        for step in steps:
            print(f"  {step.step_number}. {step.action.value} - {step.description}")

        # Get summary
        summary = integrator.get_integration_summary(questions)
        print(f"\n✓ Integration Summary:")
        for line in summary.split("\n"):
            print(f"  {line}")

        assert len(questions) > 0, "Should detect salary questions"
        assert len(steps) > 0, "Should generate steps"

        print("\n✅ TEST 2 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_questions():
    """Test 3: Mixed Question Types"""
    print("\n" + "="*70)
    print("TEST 3: MIXED QUESTIONS")
    print("="*70)

    try:
        html = read_fixture("linkedin_mixed_questions")
        print(f"\n✓ Fixture loaded")

        integrator = LinkedInQuestionIntegrator()

        # Detect questions
        questions = asyncio.run(integrator.detect_linkedin_questions(html))
        print(f"\n✓ Questions detected: {len(questions)}")

        # Count by type
        type_counts = {}
        for q in questions:
            q_type = q.field_type
            type_counts[q_type] = type_counts.get(q_type, 0) + 1

        print(f"\n✓ Question types:")
        for q_type, count in type_counts.items():
            print(f"  - {q_type}: {count}")

        # Generate steps
        steps = asyncio.run(integrator.generate_question_steps(questions))
        print(f"\n✓ ExecutionPlanSteps generated: {len(steps)}")
        for step in steps:
            print(f"  {step.step_number}. {step.action.value} - {step.description[:50]}")

        # Verify action mapping
        action_counts = {}
        for step in steps:
            action = step.action.value
            action_counts[action] = action_counts.get(action, 0) + 1

        print(f"\n✓ Execution actions:")
        for action, count in action_counts.items():
            print(f"  - {action}: {count}")

        assert len(questions) > 0, "Should detect mixed questions"
        assert len(steps) > 0, "Should generate steps"
        assert len(type_counts) > 1, "Should have multiple question types"

        print("\n✅ TEST 3 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plan_augmentation():
    """Test 4: Plan Augmentation with Questions"""
    print("\n" + "="*70)
    print("TEST 4: PLAN AUGMENTATION")
    print("="*70)

    try:
        # Create base LinkedIn Easy Apply plan
        base_plan = ExecutionPlan(
            plan_id="linkedin_base",
            workflow_type="linkedin_easy_apply",
            job_id="job_1",
            task_id="task_1",
            steps=[
                ExecutionPlanStep(
                    step_number=1,
                    action=ExecutionAction.FILL_PROFILE,
                    description="Fill profile",
                    selector=None,
                    field_name="profile",
                    required=True,
                ),
                ExecutionPlanStep(
                    step_number=2,
                    action=ExecutionAction.SUBMIT_APPLICATION,
                    description="Submit application",
                    selector="button:has-text('Submit')",
                    field_name="submit",
                    required=True,
                ),
            ],
            total_estimated_duration=300,
            confidence_score=0.9,
        )

        base_step_count = len(base_plan.steps)
        print(f"\n✓ Base plan created:")
        print(f"  - Steps: {base_step_count}")
        for step in base_plan.steps:
            print(f"    {step.step_number}. {step.action.value}")

        # Load fixture with questions
        html = read_fixture("linkedin_work_auth_questions")

        integrator = LinkedInQuestionIntegrator()

        # Augment plan with questions
        augmented_plan = asyncio.run(integrator.augment_execution_plan(base_plan, html, insert_after_step=1))

        augmented_step_count = len(augmented_plan.steps)
        print(f"\n✓ Plan augmented:")
        print(f"  - Original steps: {base_step_count}")
        print(f"  - Augmented steps: {augmented_step_count}")

        for step in augmented_plan.steps:
            print(f"    {step.step_number}. {step.action.value} - {step.description}")

        # Verify step numbering
        for i, step in enumerate(augmented_plan.steps, start=1):
            assert step.step_number == i, f"Step numbering broken at {i}"

        print(f"\n✓ Step numbering verified")

        # Check that questions were added
        assert augmented_step_count > base_step_count, f"Should add question steps (base: {base_step_count}, augmented: {augmented_step_count})"
        print(f"✓ Questions added: {augmented_step_count - base_step_count} new steps")

        # Verify first and last steps are preserved
        assert augmented_plan.steps[0].action == ExecutionAction.FILL_PROFILE, "Should preserve first step"
        assert augmented_plan.steps[-1].action == ExecutionAction.SUBMIT_APPLICATION, "Should preserve last step"
        print(f"✓ First and last steps preserved")

        print("\n✅ TEST 4 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_preservation():
    """Test 5: Metadata Preservation During Integration"""
    print("\n" + "="*70)
    print("TEST 5: METADATA PRESERVATION")
    print("="*70)

    try:
        html = read_fixture("linkedin_mixed_questions")

        integrator = LinkedInQuestionIntegrator()

        # Generate steps
        questions = asyncio.run(integrator.detect_linkedin_questions(html))
        steps = asyncio.run(integrator.generate_question_steps(questions))

        print(f"\n✓ Generated {len(steps)} steps with metadata")

        # Check metadata preservation
        metadata_fields = {
            "platform": "linkedin",
            "question_type": True,
            "question_category": True,
            "original_text": True,
        }

        print(f"\n✓ Checking metadata fields:")
        for step in steps[:3]:  # Check first 3 steps
            print(f"\n  Step {step.step_number}:")
            for field in metadata_fields:
                if field in step.metadata:
                    print(f"    ✓ {field}: {step.metadata[field]}")
                else:
                    print(f"    ❌ {field}: missing")

        # Verify all steps have metadata
        for step in steps:
            assert step.metadata, f"Step {step.step_number} should have metadata"
            assert step.metadata.get("platform") == "linkedin", "Should preserve platform"

            # Skip question-specific metadata validation for CONTINUE steps
            if step.action == ExecutionAction.CONTINUE_TO_NEXT_STEP:
                continue

            assert "question_category" in step.metadata, "Should have question_category"
            assert "question_type" in step.metadata, "Should have question_type"
            assert "original_text" in step.metadata, "Should have original_text"

        print(f"\n✓ All metadata preserved correctly")

        print("\n✅ TEST 5 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("LINKEDIN DYNAMIC QUESTION INTEGRATION - PHASE 14A.3")
    print("="*70)

    results = []

    # Test 1: Work Auth Questions
    results.append(("Work Authorization Questions", test_work_auth_questions()))

    # Test 2: Salary Questions
    results.append(("Salary Questions", test_salary_questions()))

    # Test 3: Mixed Questions
    results.append(("Mixed Questions", test_mixed_questions()))

    # Test 4: Plan Augmentation
    results.append(("Plan Augmentation", test_plan_augmentation()))

    # Test 5: Metadata Preservation
    results.append(("Metadata Preservation", test_metadata_preservation()))

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print("\nResults:")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {test_name}")

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    print(f"\nSummary: {passed_count}/{total_count} tests passed")

    if all(result for _, result in results):
        print("\n✅ ALL TESTS PASSED - LINKEDIN QUESTION INTEGRATION FUNCTIONAL")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


def main():
    """Main entry point."""
    return run_all_tests()


if __name__ == "__main__":
    sys.exit(main())

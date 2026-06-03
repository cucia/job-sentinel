"""
Phase 2 - Workflow Classification Tests

Tests workflow classification for all supported types.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_linkedin_easy_apply_classification():
    """Test LinkedIn Easy Apply classification."""
    print("\n=== Test 1: LinkedIn Easy Apply Classification ===\n")

    from backend.workflow_classification import create_classifier, WorkflowType, ExecutionStrategy

    classifier = create_classifier()

    # Test with LinkedIn URL and indicators
    result = classifier.classify(
        url="https://www.linkedin.com/jobs/view/1234567890",
        page_title="Software Engineer at Company | LinkedIn",
        page_metadata={"og:site_name": "LinkedIn"},
        dom_info={
            "easy_apply_button": True,
            "linkedin_job_card": True,
        },
    )

    print(f"✓ Classification result:")
    print(f"  - Type: {result.workflow_type.value}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Strategy: {result.execution_strategy.value}")
    print(f"  - Indicators: {result.indicators}")
    print(f"  - Reasoning: {result.reasoning}")

    assert result.workflow_type == WorkflowType.LINKEDIN_EASY_APPLY
    assert result.confidence_score > 0.5
    assert result.execution_strategy == ExecutionStrategy.LINKEDIN_EASY_APPLY_FLOW

    print("\n✅ LinkedIn Easy Apply classification verified")
    return True


def test_workday_classification():
    """Test Workday classification."""
    print("\n=== Test 2: Workday Classification ===\n")

    from backend.workflow_classification import create_classifier, WorkflowType, ExecutionStrategy

    classifier = create_classifier()

    result = classifier.classify(
        url="https://company.workday.com/careers/jobs",
        page_title="Workday Careers",
        page_metadata={"og:site_name": "Workday"},
        dom_info={
            "workday_form": True,
            "workday_iframe": True,
        },
    )

    print(f"✓ Classification result:")
    print(f"  - Type: {result.workflow_type.value}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Strategy: {result.execution_strategy.value}")
    print(f"  - Indicators: {result.indicators}")

    assert result.workflow_type == WorkflowType.WORKDAY
    assert result.confidence_score > 0.5
    assert result.execution_strategy == ExecutionStrategy.WORKDAY_FLOW

    print("\n✅ Workday classification verified")
    return True


def test_greenhouse_classification():
    """Test Greenhouse classification."""
    print("\n=== Test 3: Greenhouse Classification ===\n")

    from backend.workflow_classification import create_classifier, WorkflowType, ExecutionStrategy

    classifier = create_classifier()

    result = classifier.classify(
        url="https://boards.greenhouse.io/company/jobs/1234567",
        page_title="Greenhouse Job Board",
        page_metadata={"og:site_name": "Greenhouse"},
        dom_info={
            "greenhouse_form": True,
            "greenhouse_job_board": True,
        },
    )

    print(f"✓ Classification result:")
    print(f"  - Type: {result.workflow_type.value}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Strategy: {result.execution_strategy.value}")
    print(f"  - Indicators: {result.indicators}")

    assert result.workflow_type == WorkflowType.GREENHOUSE
    assert result.confidence_score > 0.5
    assert result.execution_strategy == ExecutionStrategy.GREENHOUSE_FLOW

    print("\n✅ Greenhouse classification verified")
    return True


def test_lever_classification():
    """Test Lever classification."""
    print("\n=== Test 4: Lever Classification ===\n")

    from backend.workflow_classification import create_classifier, WorkflowType, ExecutionStrategy

    classifier = create_classifier()

    result = classifier.classify(
        url="https://jobs.lever.co/company/abc123",
        page_title="Lever Job Posting",
        page_metadata={"og:site_name": "Lever"},
        dom_info={
            "lever_form": True,
            "lever_job_posting": True,
        },
    )

    print(f"✓ Classification result:")
    print(f"  - Type: {result.workflow_type.value}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Strategy: {result.execution_strategy.value}")
    print(f"  - Indicators: {result.indicators}")

    assert result.workflow_type == WorkflowType.LEVER
    assert result.confidence_score > 0.5
    assert result.execution_strategy == ExecutionStrategy.LEVER_FLOW

    print("\n✅ Lever classification verified")
    return True


def test_oracle_classification():
    """Test Oracle classification."""
    print("\n=== Test 5: Oracle Classification ===\n")

    from backend.workflow_classification import create_classifier, WorkflowType, ExecutionStrategy

    classifier = create_classifier()

    result = classifier.classify(
        url="https://oracle.com/careers/jobs",
        page_title="Oracle Careers",
        page_metadata={"og:site_name": "Oracle"},
        dom_info={
            "oracle_form": True,
            "oracle_careers_portal": True,
        },
    )

    print(f"✓ Classification result:")
    print(f"  - Type: {result.workflow_type.value}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Strategy: {result.execution_strategy.value}")
    print(f"  - Indicators: {result.indicators}")

    assert result.workflow_type == WorkflowType.ORACLE
    assert result.confidence_score > 0.5
    assert result.execution_strategy == ExecutionStrategy.ORACLE_FLOW

    print("\n✅ Oracle classification verified")
    return True


def test_generic_classification():
    """Test Generic workflow classification."""
    print("\n=== Test 6: Generic Workflow Classification ===\n")

    from backend.workflow_classification import create_classifier, WorkflowType, ExecutionStrategy

    classifier = create_classifier()

    result = classifier.classify(
        url="https://example.com/apply",
        page_title="Apply Now",
        page_metadata={},
        dom_info={
            "form_fields": True,
            "submit_button": True,
            "application_form": True,
        },
    )

    print(f"✓ Classification result:")
    print(f"  - Type: {result.workflow_type.value}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Strategy: {result.execution_strategy.value}")
    print(f"  - Indicators: {result.indicators}")

    assert result.workflow_type == WorkflowType.GENERIC
    assert result.confidence_score > 0.0
    assert result.execution_strategy == ExecutionStrategy.GENERIC_FORM_FLOW

    print("\n✅ Generic workflow classification verified")
    return True


def test_unknown_classification():
    """Test Unknown workflow classification."""
    print("\n=== Test 7: Unknown Workflow Classification ===\n")

    from backend.workflow_classification import create_classifier, WorkflowType, ExecutionStrategy

    classifier = create_classifier()

    result = classifier.classify(
        url="https://unknown.example.com/page",
        page_title="Unknown Page",
        page_metadata={},
        dom_info={},
    )

    print(f"✓ Classification result:")
    print(f"  - Type: {result.workflow_type.value}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Strategy: {result.execution_strategy.value}")
    print(f"  - Reasoning: {result.reasoning}")

    assert result.workflow_type == WorkflowType.UNKNOWN
    assert result.confidence_score == 0.0
    assert result.execution_strategy == ExecutionStrategy.MANUAL_REVIEW

    print("\n✅ Unknown workflow classification verified")
    return True


def test_confidence_scoring():
    """Test confidence scoring."""
    print("\n=== Test 8: Confidence Scoring ===\n")

    from backend.workflow_classification import create_classifier

    classifier = create_classifier()

    # Test with minimal indicators
    result_minimal = classifier.classify(
        url="https://www.linkedin.com/jobs/view/1234567890",
        page_title=None,
        page_metadata={},
        dom_info={},
    )

    print(f"✓ Minimal indicators:")
    print(f"  - Confidence: {result_minimal.confidence_score:.2f}")

    # Test with full indicators
    result_full = classifier.classify(
        url="https://www.linkedin.com/jobs/view/1234567890",
        page_title="Software Engineer at Company | LinkedIn",
        page_metadata={"og:site_name": "LinkedIn"},
        dom_info={
            "easy_apply_button": True,
            "linkedin_job_card": True,
        },
    )

    print(f"✓ Full indicators:")
    print(f"  - Confidence: {result_full.confidence_score:.2f}")

    # Full should have higher confidence than minimal
    assert result_full.confidence_score > result_minimal.confidence_score

    print("\n✅ Confidence scoring verified")
    return True


def test_multiple_indicators():
    """Test classification with multiple indicators."""
    print("\n=== Test 9: Multiple Indicators ===\n")

    from backend.workflow_classification import create_classifier, WorkflowType

    classifier = create_classifier()

    result = classifier.classify(
        url="https://boards.greenhouse.io/company/jobs/1234567",
        page_title="Greenhouse Job Board - Software Engineer",
        page_metadata={
            "og:site_name": "Greenhouse",
            "og:title": "Software Engineer",
        },
        dom_info={
            "greenhouse_form": True,
            "greenhouse_job_board": True,
            "job_title": True,
            "job_description": True,
        },
    )

    print(f"✓ Classification with multiple indicators:")
    print(f"  - Type: {result.workflow_type.value}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Indicators found: {len(result.indicators)}")
    print(f"  - Indicators: {list(result.indicators.keys())}")

    assert result.workflow_type == WorkflowType.GREENHOUSE
    assert len(result.indicators) > 0

    print("\n✅ Multiple indicators classification verified")
    return True


def main():
    """Run all workflow classification tests."""
    print("\n" + "="*70)
    print("PHASE 2 - WORKFLOW CLASSIFICATION TESTS")
    print("="*70)

    results = {}

    # Run all tests
    results["linkedin_easy_apply"] = test_linkedin_easy_apply_classification()
    results["workday"] = test_workday_classification()
    results["greenhouse"] = test_greenhouse_classification()
    results["lever"] = test_lever_classification()
    results["oracle"] = test_oracle_classification()
    results["generic"] = test_generic_classification()
    results["unknown"] = test_unknown_classification()
    results["confidence_scoring"] = test_confidence_scoring()
    results["multiple_indicators"] = test_multiple_indicators()

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
        print("✅ PHASE 2 WORKFLOW CLASSIFICATION COMPLETE")
        print("="*70)
        print("\nSupported workflows:")
        print("  ✅ LinkedIn Easy Apply")
        print("  ✅ Workday")
        print("  ✅ Greenhouse")
        print("  ✅ Lever")
        print("  ✅ Oracle")
        print("  ✅ Generic/Unknown")
        print("\nClassification features:")
        print("  ✅ URL-based detection")
        print("  ✅ Metadata-based detection")
        print("  ✅ DOM-based detection")
        print("  ✅ Confidence scoring")
        print("  ✅ Indicator tracking")
        print("  ✅ Execution strategy selection")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

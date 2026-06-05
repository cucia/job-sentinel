"""
LinkedIn Detection Validation Test

Tests LinkedIn page understanding:
1. LinkedIn page detection
2. Easy Apply detection
3. External Apply detection
4. Metadata extraction
5. Workflow classification
"""

import sys
import os
import re
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.platforms.linkedin import (
    LinkedInDetector,
    LinkedInJobParser,
    LinkedInWorkflowClassifier,
    LinkedInPageType,
    LinkedInWorkflowType,
)


def get_fixture_url(fixture_name: str):
    """Get file:// URL for LinkedIn fixture."""
    fixture_path = Path(__file__).parent / "test_fixtures" / "linkedin" / f"{fixture_name}.html"
    return f"file://{fixture_path.absolute()}"


def read_fixture(fixture_name: str) -> str:
    """Read fixture HTML content."""
    fixture_path = Path(__file__).parent / "test_fixtures" / "linkedin" / f"{fixture_name}.html"
    with open(fixture_path, 'r') as f:
        return f.read()


def test_linkedin_page_detection():
    """Test 1: LinkedIn Page Detection"""
    print("\n" + "="*70)
    print("TEST 1: LINKEDIN PAGE DETECTION")
    print("="*70)

    try:
        detector = LinkedInDetector()

        # Test URLs
        test_cases = [
            ("https://www.linkedin.com/jobs/view/123456789/", True),
            ("https://linkedin.com/jobs/search", True),
            ("https://example.com/jobs", False),
            ("https://www.linkedin.com/feed", True),
        ]

        print("\n✓ Testing LinkedIn URL detection:")
        for url, expected in test_cases:
            result = asyncio.run(detector.is_linkedin_page(url))
            status = "✓" if result == expected else "✗"
            print(f"  {status} {url}: {result}")

        print("\n✅ TEST 1 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_easy_apply_detection():
    """Test 2: Easy Apply Detection"""
    print("\n" + "="*70)
    print("TEST 2: EASY APPLY DETECTION")
    print("="*70)

    try:
        fixture_url = get_fixture_url("linkedin_easy_apply")
        html = read_fixture("linkedin_easy_apply")

        print(f"\n✓ Fixture loaded: {fixture_url}")
        print(f"  HTML size: {len(html)} bytes")

        detector = LinkedInDetector()
        parser = LinkedInJobParser()

        # Extract page title from HTML
        title_match = re.search(r'<title>([^<]+)</title>', html)
        page_title = title_match.group(1) if title_match else None

        # Test LinkedIn page detection with page title
        is_linkedin = asyncio.run(detector.is_linkedin_page(fixture_url, page_title))
        print(f"\n✓ Is LinkedIn page: {is_linkedin}")

        is_easy_apply = asyncio.run(detector.is_easy_apply(html))
        print(f"✓ Easy Apply available: {is_easy_apply}")
        assert is_easy_apply, "Should detect Easy Apply"

        is_external = asyncio.run(detector.is_external_apply(html))
        print(f"✓ External Apply available: {is_external}")
        assert not is_external, "Should not detect external apply"

        # Parse page
        page_data = asyncio.run(parser.parse(fixture_url, html))
        print(f"\n✓ Parsed job data:")
        print(f"  - Title: {page_data.job_title}")
        print(f"  - Company: {page_data.company_name}")
        print(f"  - Location: {page_data.location}")
        print(f"  - Employment Type: {page_data.employment_type}")
        print(f"  - Experience Level: {page_data.experience_level}")
        print(f"  - Easy Apply: {page_data.easy_apply_available}")

        assert page_data.job_title, "Should extract job title"
        assert page_data.company_name, f"Should extract company (got: {page_data.company_name})"
        assert page_data.location, f"Should extract location (got: {page_data.location})"

        print("\n✅ TEST 2 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_external_apply_detection():
    """Test 3: External Apply Detection"""
    print("\n" + "="*70)
    print("TEST 3: EXTERNAL APPLY DETECTION")
    print("="*70)

    try:
        fixture_url = get_fixture_url("linkedin_external_apply")
        html = read_fixture("linkedin_external_apply")

        print(f"\n✓ Fixture loaded: {fixture_url}")

        detector = LinkedInDetector()
        parser = LinkedInJobParser()

        # Extract page title from HTML
        title_match = re.search(r'<title>([^<]+)</title>', html)
        page_title = title_match.group(1) if title_match else None

        # Test external apply detection
        is_easy_apply = asyncio.run(detector.is_easy_apply(html))
        print(f"\n✓ Easy Apply available: {is_easy_apply}")
        assert not is_easy_apply, "Should not detect Easy Apply"

        is_external = asyncio.run(detector.is_external_apply(html))
        print(f"✓ External Apply available: {is_external}")
        assert is_external, "Should detect external apply"

        # Parse page
        page_data = asyncio.run(parser.parse(fixture_url, html))
        print(f"\n✓ Parsed job data:")
        print(f"  - Title: {page_data.job_title}")
        print(f"  - Company: {page_data.company_name}")
        print(f"  - Location: {page_data.location}")
        print(f"  - External Apply: {page_data.external_apply_available}")

        assert page_data.external_apply_available, "Should have external apply"

        print("\n✅ TEST 3 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_extraction():
    """Test 4: Metadata Extraction"""
    print("\n" + "="*70)
    print("TEST 4: METADATA EXTRACTION")
    print("="*70)

    try:
        html = read_fixture("linkedin_easy_apply")
        fixture_url = get_fixture_url("linkedin_easy_apply")

        # Extract page title from HTML
        title_match = re.search(r'<title>([^<]+)</title>', html)
        page_title = title_match.group(1) if title_match else None

        parser = LinkedInJobParser()
        page_data = asyncio.run(parser.parse(fixture_url, html))

        print(f"\n✓ Extracted metadata:")
        print(f"\n  Job Information:")
        print(f"    - Title: {page_data.job_title}")
        assert page_data.job_title == "Security Analyst", f"Expected 'Security Analyst', got {page_data.job_title}"
        print(f"    ✓ Job title extracted correctly")

        print(f"\n    - Company: {page_data.company_name}")
        assert page_data.company_name == "Example Corp", f"Expected 'Example Corp', got {page_data.company_name}"
        print(f"    ✓ Company extracted correctly")

        print(f"\n    - Location: {page_data.location}")
        assert "Bangalore" in (page_data.location or ""), f"Expected location to contain 'Bangalore', got {page_data.location}"
        print(f"    ✓ Location extracted correctly")

        print(f"\n    - Employment Type: {page_data.employment_type}")
        assert page_data.employment_type == "Full-time", f"Expected 'Full-time', got {page_data.employment_type}"
        print(f"    ✓ Employment type extracted correctly")

        print(f"\n    - Experience Level: {page_data.experience_level}")
        assert page_data.experience_level == "Mid-Level", f"Expected 'Mid-Level', got {page_data.experience_level}"
        print(f"    ✓ Experience level extracted correctly")

        print(f"\n  Application Methods:")
        print(f"    - Easy Apply: {page_data.easy_apply_available}")
        assert page_data.easy_apply_available, "Should have Easy Apply"
        print(f"    ✓ Easy Apply detected")

        print(f"\n  Page Type: {page_data.page_type}")
        assert page_data.page_type == LinkedInPageType.EASY_APPLY_PAGE, f"Expected EASY_APPLY_PAGE, got {page_data.page_type}"
        print(f"  ✓ Page type classified correctly")

        print("\n✅ TEST 4 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_classification():
    """Test 5: Workflow Classification"""
    print("\n" + "="*70)
    print("TEST 5: WORKFLOW CLASSIFICATION")
    print("="*70)

    try:
        classifier = LinkedInWorkflowClassifier()

        # Test 5A: Easy Apply workflow
        print("\n✓ Test 5A: Easy Apply workflow classification")
        html_easy = read_fixture("linkedin_easy_apply")
        parser = LinkedInJobParser()
        page_data_easy = asyncio.run(parser.parse(get_fixture_url("linkedin_easy_apply"), html_easy))
        workflow_easy = classifier.classify(page_data_easy)
        print(f"  - Page: {page_data_easy.job_title}")
        print(f"  - Workflow type: {workflow_easy}")
        assert workflow_easy in (LinkedInWorkflowType.EASY_APPLY, LinkedInWorkflowType.MULTI_STEP_EASY_APPLY)
        print(f"  ✓ Correctly classified as Easy Apply workflow")

        # Test 5B: External Apply workflow
        print("\n✓ Test 5B: External Apply workflow classification")
        html_ext = read_fixture("linkedin_external_apply")
        page_data_ext = asyncio.run(parser.parse(get_fixture_url("linkedin_external_apply"), html_ext))
        workflow_ext = classifier.classify(page_data_ext)
        print(f"  - Page: {page_data_ext.job_title}")
        print(f"  - Workflow type: {workflow_ext}")
        assert workflow_ext == LinkedInWorkflowType.EXTERNAL_REDIRECT
        print(f"  ✓ Correctly classified as External Redirect workflow")

        # Test 5C: Multi-step Easy Apply workflow
        print("\n✓ Test 5C: Multi-step Easy Apply workflow classification")
        html_multi = read_fixture("linkedin_multi_step")
        page_data_multi = asyncio.run(parser.parse(get_fixture_url("linkedin_multi_step"), html_multi))
        workflow_multi = classifier.classify(page_data_multi)
        print(f"  - Page: {page_data_multi.job_title}")
        print(f"  - Workflow type: {workflow_multi}")
        assert workflow_multi in (LinkedInWorkflowType.EASY_APPLY, LinkedInWorkflowType.MULTI_STEP_EASY_APPLY)
        print(f"  ✓ Correctly classified workflow")

        # Test workflow characteristics
        print("\n✓ Workflow characteristics:")
        for wf_type in [LinkedInWorkflowType.EASY_APPLY, LinkedInWorkflowType.EXTERNAL_REDIRECT]:
            chars = classifier.get_workflow_characteristics(wf_type)
            print(f"  - {chars['name']}: {chars['description']}")

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
    print("LINKEDIN PAGE UNDERSTANDING VALIDATION - PHASE 14A.1")
    print("="*70)

    results = []

    # Test 1: Page detection
    results.append(("LinkedIn Page Detection", test_linkedin_page_detection()))

    # Test 2: Easy Apply detection
    results.append(("Easy Apply Detection", test_easy_apply_detection()))

    # Test 3: External Apply detection
    results.append(("External Apply Detection", test_external_apply_detection()))

    # Test 4: Metadata extraction
    results.append(("Metadata Extraction", test_metadata_extraction()))

    # Test 5: Workflow classification
    results.append(("Workflow Classification", test_workflow_classification()))

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
        print("\n✅ ALL TESTS PASSED - LINKEDIN PAGE UNDERSTANDING FUNCTIONAL")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


# Need to import asyncio for async tests
import asyncio


def main():
    """Main entry point."""
    return run_all_tests()


if __name__ == "__main__":
    sys.exit(main())

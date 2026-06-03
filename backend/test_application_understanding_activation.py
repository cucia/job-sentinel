"""
Application Understanding Pipeline Activation Tests

Validates that the complete pipeline is now connected and executed:
PageDataProducer → PageAnalyzer → ExecutionPlanner

Tests three scenarios:
A. Task with no page_data (awaiting_page_data)
B. Task with page_data (analysis and plan executed)
C. Task with raw_page (producer, analysis, plan executed)
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.runtime.task_model import Task, TaskStatus
from backend.workflow.handlers import LinkedInEasyApplyHandler, IndeedHandler, NaukriHandler
from backend.application.page_data_producer import PageDataProducer
import json


# Representative HTML fixtures
LINKEDIN_HTML = """
<html>
<head><title>Apply - LinkedIn</title></head>
<body>
<form id="profile_form" name="profile">
    <label for="fname">First Name</label>
    <input id="fname" type="text" name="firstName" required />
    <label for="email">Email</label>
    <input id="email" type="email" name="email" required />
</form>
<button id="next_btn" type="submit">Next</button>
</body>
</html>
"""

INDEED_HTML = """
<html>
<head><title>Apply Now - Indeed</title></head>
<body>
<form id="resume_form" name="upload">
    <label for="resume_upload">Upload Resume</label>
    <input id="resume_upload" type="file" name="resume" required />
</form>
<form id="profile_form" name="profile">
    <label for="email">Email</label>
    <input id="email" type="email" name="email" required />
</form>
<button id="apply_btn" type="submit">Apply Now</button>
</body>
</html>
"""

NAUKRI_HTML = """
<html>
<head><title>Apply - Naukri</title></head>
<body>
<form id="profile_form" name="profile">
    <label for="name">Full Name</label>
    <input id="name" type="text" name="fullName" required />
    <label for="skills">Key Skills</label>
    <textarea id="skills" name="keySkills" required></textarea>
</form>
<button id="submit_btn" type="submit">Submit Application</button>
</body>
</html>
"""


def test_linkedin_no_page_data():
    """Test A.1: LinkedIn task without page_data → awaiting_page_data."""
    print("\n=== Test A.1: LinkedIn - No Page Data ===\n")

    try:
        handler = LinkedInEasyApplyHandler()

        task = Task(
            task_id="test_a1",
            job_id="job_001",
            source_platform="linkedin",
            status=TaskStatus.QUEUED,
            workflow_type="linkedin_easy_apply",
            execution_strategy="linkedin_easy_apply_flow",
            workflow_confidence=0.95,
            metadata={
                "job": {
                    "title": "Software Engineer",
                    "url": "https://www.linkedin.com/jobs/view/123",
                }
            },
        )

        print("✓ Executing handler.prepare_for_processing()")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - reason: {result.get('reason')}")

        # Verify awaiting_page_data status
        assert result["valid"] == True
        assert result.get("ready_for_execution") == False
        assert result.get("reason") == "awaiting_page_data"
        assert result.get("session") is not None

        print("✅ Correctly returns awaiting_page_data")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indeed_no_page_data():
    """Test A.2: Indeed task without page_data → awaiting_page_data."""
    print("\n=== Test A.2: Indeed - No Page Data ===\n")

    try:
        handler = IndeedHandler()

        task = Task(
            task_id="test_a2",
            job_id="job_002",
            source_platform="indeed",
            status=TaskStatus.QUEUED,
            workflow_type="indeed",
            execution_strategy="generic_form_flow",
            workflow_confidence=0.85,
            metadata={
                "job": {
                    "title": "Data Scientist",
                    "url": "https://indeed.com/viewjob?jk=123",
                }
            },
        )

        print("✓ Executing handler.prepare_for_processing()")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - reason: {result.get('reason')}")

        # Verify awaiting_page_data status
        assert result["valid"] == True
        assert result.get("ready_for_execution") == False
        assert result.get("reason") == "awaiting_page_data"
        assert result.get("session") is not None

        print("✅ Correctly returns awaiting_page_data")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_naukri_no_page_data():
    """Test A.3: Naukri task without page_data → awaiting_page_data."""
    print("\n=== Test A.3: Naukri - No Page Data ===\n")

    try:
        handler = NaukriHandler()

        task = Task(
            task_id="test_a3",
            job_id="job_003",
            source_platform="naukri",
            status=TaskStatus.QUEUED,
            workflow_type="naukri",
            execution_strategy="generic_form_flow",
            workflow_confidence=0.80,
            metadata={
                "job": {
                    "title": "Product Manager",
                    "url": "https://naukri.com/job/123",
                }
            },
        )

        print("✓ Executing handler.prepare_for_processing()")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - reason: {result.get('reason')}")

        # Verify awaiting_page_data status
        assert result["valid"] == True
        assert result.get("ready_for_execution") == False
        assert result.get("reason") == "awaiting_page_data"
        assert result.get("session") is not None

        print("✅ Correctly returns awaiting_page_data")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_linkedin_with_page_data():
    """Test B.1: LinkedIn task with page_data → analysis and plan executed."""
    print("\n=== Test B.1: LinkedIn - With Page Data ===\n")

    try:
        handler = LinkedInEasyApplyHandler()
        producer = PageDataProducer()

        # Produce page_data from HTML
        raw_page = {
            "url": "https://www.linkedin.com/jobs/view/123",
            "title": "Apply - LinkedIn",
            "html": LINKEDIN_HTML,
            "platform": "linkedin",
        }
        page_data = producer.produce(raw_page)

        task = Task(
            task_id="test_b1",
            job_id="job_001",
            source_platform="linkedin",
            status=TaskStatus.QUEUED,
            workflow_type="linkedin_easy_apply",
            execution_strategy="linkedin_easy_apply_flow",
            workflow_confidence=0.95,
            metadata={
                "job": {"title": "Engineer", "url": "https://www.linkedin.com/jobs/view/123"},
                "page_data": page_data,
            },
        )

        print("✓ Page data available, executing handler")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - page_analysis present: {'page_analysis' in result}")
        print(f"  - execution_plan present: {'execution_plan' in result}")

        # Verify analysis and planning executed
        assert result["valid"] == True
        assert result.get("ready_for_execution") == True
        assert result.get("page_analysis") is not None
        assert result.get("execution_plan") is not None
        assert result.get("session") is not None

        print("✅ Analysis and planning executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indeed_with_page_data():
    """Test B.2: Indeed task with page_data → analysis and plan executed."""
    print("\n=== Test B.2: Indeed - With Page Data ===\n")

    try:
        handler = IndeedHandler()
        producer = PageDataProducer()

        # Produce page_data from HTML
        raw_page = {
            "url": "https://indeed.com/viewjob?jk=123",
            "title": "Apply Now - Indeed",
            "html": INDEED_HTML,
            "platform": "indeed",
        }
        page_data = producer.produce(raw_page)

        task = Task(
            task_id="test_b2",
            job_id="job_002",
            source_platform="indeed",
            status=TaskStatus.QUEUED,
            workflow_type="indeed",
            execution_strategy="generic_form_flow",
            workflow_confidence=0.85,
            metadata={
                "job": {"title": "Scientist", "url": "https://indeed.com/viewjob?jk=123"},
                "page_data": page_data,
            },
        )

        print("✓ Page data available, executing handler")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - page_analysis present: {'page_analysis' in result}")
        print(f"  - execution_plan present: {'execution_plan' in result}")

        # Verify analysis and planning executed
        assert result["valid"] == True
        assert result.get("ready_for_execution") == True
        assert result.get("page_analysis") is not None
        assert result.get("execution_plan") is not None

        print("✅ Analysis and planning executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_naukri_with_page_data():
    """Test B.3: Naukri task with page_data → analysis and plan executed."""
    print("\n=== Test B.3: Naukri - With Page Data ===\n")

    try:
        handler = NaukriHandler()
        producer = PageDataProducer()

        # Produce page_data from HTML
        raw_page = {
            "url": "https://naukri.com/job/123",
            "title": "Apply - Naukri",
            "html": NAUKRI_HTML,
            "platform": "naukri",
        }
        page_data = producer.produce(raw_page)

        task = Task(
            task_id="test_b3",
            job_id="job_003",
            source_platform="naukri",
            status=TaskStatus.QUEUED,
            workflow_type="naukri",
            execution_strategy="generic_form_flow",
            workflow_confidence=0.80,
            metadata={
                "job": {"title": "Manager", "url": "https://naukri.com/job/123"},
                "page_data": page_data,
            },
        )

        print("✓ Page data available, executing handler")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - page_analysis present: {'page_analysis' in result}")
        print(f"  - execution_plan present: {'execution_plan' in result}")

        # Verify analysis and planning executed
        assert result["valid"] == True
        assert result.get("ready_for_execution") == True
        assert result.get("page_analysis") is not None
        assert result.get("execution_plan") is not None

        print("✅ Analysis and planning executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_linkedin_with_raw_page():
    """Test C.1: LinkedIn task with raw_page → producer, analysis, plan executed."""
    print("\n=== Test C.1: LinkedIn - With Raw Page ===\n")

    try:
        handler = LinkedInEasyApplyHandler()

        task = Task(
            task_id="test_c1",
            job_id="job_001",
            source_platform="linkedin",
            status=TaskStatus.QUEUED,
            workflow_type="linkedin_easy_apply",
            execution_strategy="linkedin_easy_apply_flow",
            workflow_confidence=0.95,
            metadata={
                "job": {"title": "Engineer", "url": "https://www.linkedin.com/jobs/view/123"},
                "raw_page": {
                    "url": "https://www.linkedin.com/jobs/view/123",
                    "title": "Apply - LinkedIn",
                    "html": LINKEDIN_HTML,
                    "platform": "linkedin",
                },
            },
        )

        print("✓ Raw page available, executing handler")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - page_analysis present: {'page_analysis' in result}")
        print(f"  - execution_plan present: {'execution_plan' in result}")

        # Verify producer → analysis → planning executed
        assert result["valid"] == True
        assert result.get("ready_for_execution") == True
        assert result.get("page_analysis") is not None
        assert result.get("execution_plan") is not None

        print("✅ Producer, analysis, and planning executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indeed_with_raw_page():
    """Test C.2: Indeed task with raw_page → producer, analysis, plan executed."""
    print("\n=== Test C.2: Indeed - With Raw Page ===\n")

    try:
        handler = IndeedHandler()

        task = Task(
            task_id="test_c2",
            job_id="job_002",
            source_platform="indeed",
            status=TaskStatus.QUEUED,
            workflow_type="indeed",
            execution_strategy="generic_form_flow",
            workflow_confidence=0.85,
            metadata={
                "job": {"title": "Scientist", "url": "https://indeed.com/viewjob?jk=123"},
                "raw_page": {
                    "url": "https://indeed.com/viewjob?jk=123",
                    "title": "Apply Now - Indeed",
                    "html": INDEED_HTML,
                    "platform": "indeed",
                },
            },
        )

        print("✓ Raw page available, executing handler")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - page_analysis present: {'page_analysis' in result}")
        print(f"  - execution_plan present: {'execution_plan' in result}")

        # Verify producer → analysis → planning executed
        assert result["valid"] == True
        assert result.get("ready_for_execution") == True
        assert result.get("page_analysis") is not None
        assert result.get("execution_plan") is not None

        print("✅ Producer, analysis, and planning executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_naukri_with_raw_page():
    """Test C.3: Naukri task with raw_page → producer, analysis, plan executed."""
    print("\n=== Test C.3: Naukri - With Raw Page ===\n")

    try:
        handler = NaukriHandler()

        task = Task(
            task_id="test_c3",
            job_id="job_003",
            source_platform="naukri",
            status=TaskStatus.QUEUED,
            workflow_type="naukri",
            execution_strategy="generic_form_flow",
            workflow_confidence=0.80,
            metadata={
                "job": {"title": "Manager", "url": "https://naukri.com/job/123"},
                "raw_page": {
                    "url": "https://naukri.com/job/123",
                    "title": "Apply - Naukri",
                    "html": NAUKRI_HTML,
                    "platform": "naukri",
                },
            },
        )

        print("✓ Raw page available, executing handler")
        result = handler.prepare_for_processing(task)

        print(f"  - valid: {result['valid']}")
        print(f"  - ready_for_execution: {result.get('ready_for_execution')}")
        print(f"  - page_analysis present: {'page_analysis' in result}")
        print(f"  - execution_plan present: {'execution_plan' in result}")

        # Verify producer → analysis → planning executed
        assert result["valid"] == True
        assert result.get("ready_for_execution") == True
        assert result.get("page_analysis") is not None
        assert result.get("execution_plan") is not None

        print("✅ Producer, analysis, and planning executed successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("APPLICATION UNDERSTANDING PIPELINE ACTIVATION")
    print("PageDataProducer → PageAnalyzer → ExecutionPlanner")
    print("="*70)

    results = {}

    # Scenario A: No page data
    results["a1_linkedin_no_page_data"] = test_linkedin_no_page_data()
    results["a2_indeed_no_page_data"] = test_indeed_no_page_data()
    results["a3_naukri_no_page_data"] = test_naukri_no_page_data()

    # Scenario B: With page data
    results["b1_linkedin_with_page_data"] = test_linkedin_with_page_data()
    results["b2_indeed_with_page_data"] = test_indeed_with_page_data()
    results["b3_naukri_with_page_data"] = test_naukri_with_page_data()

    # Scenario C: With raw page
    results["c1_linkedin_with_raw_page"] = test_linkedin_with_raw_page()
    results["c2_indeed_with_raw_page"] = test_indeed_with_raw_page()
    results["c3_naukri_with_raw_page"] = test_naukri_with_raw_page()

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print("\nScenario A - No Page Data (awaiting_page_data):")
    for key, result in list(results.items())[:3]:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {key}")

    print("\nScenario B - With Page Data (analysis + planning):")
    for key, result in list(results.items())[3:6]:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {key}")

    print("\nScenario C - With Raw Page (producer + analysis + planning):")
    for key, result in list(results.items())[6:]:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {key}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*70)
        print("✅ APPLICATION UNDERSTANDING PIPELINE ACTIVATED")
        print("="*70)
        print("\nPipeline Status:")
        print("  ✅ PageDataProducer connected")
        print("  ✅ PageAnalyzer integrated")
        print("  ✅ ExecutionPlanner integrated")
        print("  ✅ All three platforms working (LinkedIn, Indeed, Naukri)")
        print("\nCapabilities:")
        print("  • Tasks without page_data return awaiting_page_data")
        print("  • Tasks with page_data execute analysis and planning")
        print("  • Tasks with raw_page run producer → analysis → planning")
        print("\nReady for:")
        print("  • Browser automation integration (Phase 4+)")
        print("  • Application execution (Phase 5+)")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

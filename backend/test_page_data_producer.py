"""
Page Data Producer Validation Tests

Validates HTML → page_data → PageAnalyzer → ExecutionPlanner flow

Tests representative HTML for:
- LinkedIn
- Indeed
- Naukri
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.application.page_data_producer import PageDataProducer
from backend.application.page_analyzer import create_page_analyzer
from backend.application.execution_planner import create_execution_planner
from backend.application.session import ApplicationSession
from backend.runtime.task_model import Task, TaskStatus


# LinkedIn representative HTML
LINKEDIN_PROFILE_HTML = """
<html>
<head><title>Apply - LinkedIn</title></head>
<body>
<form id="profile_form" name="profile">
    <label for="fname">First Name</label>
    <input id="fname" type="text" name="firstName" required />

    <label for="lname">Last Name</label>
    <input id="lname" type="text" name="lastName" required />

    <label for="email">Email</label>
    <input id="email" type="email" name="email" required />

    <label for="phone">Phone</label>
    <input id="phone" type="tel" name="phone" />
</form>
<button id="next_btn" type="submit">Next</button>
</body>
</html>
"""

# Indeed representative HTML
INDEED_APPLICATION_HTML = """
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

    <label for="phone">Phone</label>
    <input id="phone" type="tel" name="phone" />

    <label for="experience">Years of Experience</label>
    <select id="experience" name="yearsOfExperience">
        <option value="">Select</option>
        <option value="0-1">0-1 years</option>
        <option value="1-3">1-3 years</option>
        <option value="3-5">3-5 years</option>
    </select>
</form>
<button id="apply_btn" type="submit">Apply Now</button>
</body>
</html>
"""

# Naukri representative HTML
NAUKRI_APPLICATION_HTML = """
<html>
<head><title>Apply - Naukri</title></head>
<body>
<form id="profile_form" name="profile">
    <label for="name">Full Name</label>
    <input id="name" type="text" name="fullName" required />

    <label for="skills">Key Skills</label>
    <textarea id="skills" name="keySkills" required></textarea>

    <label for="experience">Current Company</label>
    <input id="experience" type="text" name="currentCompany" />

    <label for="designation">Current Designation</label>
    <input id="designation" type="text" name="currentDesignation" />
</form>
<button id="submit_btn" type="submit">Submit Application</button>
</body>
</html>
"""


def test_linkedin_html_to_page_data():
    """Test 1: LinkedIn HTML → page_data extraction."""
    print("\n=== Test 1: LinkedIn HTML to Page Data ===\n")

    try:
        producer = PageDataProducer()

        raw_page = {
            "url": "https://www.linkedin.com/jobs/view/123/apply",
            "title": "Apply - LinkedIn",
            "html": LINKEDIN_PROFILE_HTML,
            "platform": "linkedin",
        }

        print("✓ Extracting page data from LinkedIn HTML")
        page_data = producer.produce(raw_page)

        # Verify contract
        assert "url" in page_data
        assert "title" in page_data
        assert "platform" in page_data
        assert "forms" in page_data
        assert "fields" in page_data
        assert "buttons" in page_data
        assert "links" in page_data
        assert "page_type" in page_data
        assert "metadata" in page_data

        print(f"  - URL: {page_data['url']}")
        print(f"  - Title: {page_data['title']}")
        print(f"  - Platform: {page_data['platform']}")
        print(f"  - Page type: {page_data['page_type']}")
        print(f"  - Forms: {len(page_data['forms'])}")
        print(f"  - Fields: {len(page_data['fields'])}")
        print(f"  - Buttons: {len(page_data['buttons'])}")

        # Verify extraction
        assert page_data["page_type"] == "linkedin_application"
        assert len(page_data["forms"]) > 0
        assert len(page_data["fields"]) >= 4  # fname, lname, email, phone
        assert len(page_data["buttons"]) > 0

        # Verify fields
        field_names = [f["name"] for f in page_data["fields"]]
        assert "firstName" in field_names
        assert "lastName" in field_names
        assert "email" in field_names

        print("✅ LinkedIn HTML extraction verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indeed_html_to_page_data():
    """Test 2: Indeed HTML → page_data extraction."""
    print("\n=== Test 2: Indeed HTML to Page Data ===\n")

    try:
        producer = PageDataProducer()

        raw_page = {
            "url": "https://indeed.com/viewjob?jk=123/apply",
            "title": "Apply Now - Indeed",
            "html": INDEED_APPLICATION_HTML,
            "platform": "indeed",
        }

        print("✓ Extracting page data from Indeed HTML")
        page_data = producer.produce(raw_page)

        print(f"  - Page type: {page_data['page_type']}")
        print(f"  - Forms: {len(page_data['forms'])}")
        print(f"  - Fields: {len(page_data['fields'])}")
        print(f"  - Buttons: {len(page_data['buttons'])}")

        # Verify extraction
        assert page_data["page_type"] == "indeed_application"
        assert len(page_data["forms"]) >= 2  # resume_form and profile_form
        assert len(page_data["fields"]) >= 4  # resume, email, phone, experience
        assert len(page_data["buttons"]) > 0

        # Verify file upload detection
        field_types = [f["type"] for f in page_data["fields"]]
        assert "file" in field_types

        # Verify select field
        select_fields = [f for f in page_data["fields"] if f["type"] == "select"]
        assert len(select_fields) > 0
        assert len(select_fields[0].get("options", [])) > 0

        print("✅ Indeed HTML extraction verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_naukri_html_to_page_data():
    """Test 3: Naukri HTML → page_data extraction."""
    print("\n=== Test 3: Naukri HTML to Page Data ===\n")

    try:
        producer = PageDataProducer()

        raw_page = {
            "url": "https://naukri.com/job/123/apply",
            "title": "Apply - Naukri",
            "html": NAUKRI_APPLICATION_HTML,
            "platform": "naukri",
        }

        print("✓ Extracting page data from Naukri HTML")
        page_data = producer.produce(raw_page)

        print(f"  - Page type: {page_data['page_type']}")
        print(f"  - Forms: {len(page_data['forms'])}")
        print(f"  - Fields: {len(page_data['fields'])}")
        print(f"  - Buttons: {len(page_data['buttons'])}")

        # Verify extraction
        assert page_data["page_type"] == "naukri_application"
        assert len(page_data["forms"]) > 0
        assert len(page_data["fields"]) >= 4  # name, skills, company, designation
        assert len(page_data["buttons"]) > 0

        # Verify textarea detection
        field_types = [f["type"] for f in page_data["fields"]]
        assert "textarea" in field_types

        print("✅ Naukri HTML extraction verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_page_data_to_analyzer():
    """Test 4: page_data → PageAnalyzer → ExecutionPlanner."""
    print("\n=== Test 4: Page Data to Analyzer to Planner ===\n")

    try:
        producer = PageDataProducer()
        analyzer = create_page_analyzer()
        planner = create_execution_planner("indeed")

        # Extract LinkedIn page data
        raw_page = {
            "url": "https://www.linkedin.com/jobs/view/123/apply",
            "title": "Apply - LinkedIn",
            "html": LINKEDIN_PROFILE_HTML,
            "platform": "linkedin",
        }

        print("✓ Step 1: Produce page_data from HTML")
        page_data = producer.produce(raw_page)
        print(f"  - Fields extracted: {len(page_data['fields'])}")

        print("✓ Step 2: Analyze page_data")
        analysis = analyzer.analyze_page(page_data)
        print(f"  - Page type: {analysis.page_type}")
        print(f"  - Forms found: {len(analysis.forms)}")
        print(f"  - Fields found: {len(analysis.visible_fields)}")

        print("✓ Step 3: Generate execution plan")
        plan = planner.generate_plan(
            job_id="job_001",
            task_id="task_001",
            page_analysis=analysis,
        )
        print(f"  - Plan steps: {len(plan.steps)}")
        print(f"  - Confidence: {plan.confidence_score:.0%}")

        # Verify complete flow
        assert page_data is not None
        assert analysis is not None
        assert plan is not None
        assert len(plan.steps) > 0

        print("✅ Complete flow verified (HTML → page_data → analysis → plan)")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_page_data_contract():
    """Test 5: Verify strict page_data contract."""
    print("\n=== Test 5: Page Data Contract ===\n")

    try:
        producer = PageDataProducer()

        raw_page = {
            "url": "https://example.com/apply",
            "title": "Application",
            "html": "<html></html>",
            "platform": "unknown",
        }

        print("✓ Producing page_data with unknown platform")
        page_data = producer.produce(raw_page)

        # Verify EXACTLY these top-level keys exist
        required_keys = {"url", "title", "platform", "forms", "fields", "buttons", "links", "page_type", "metadata"}
        actual_keys = set(page_data.keys())

        print(f"  - Required keys: {required_keys}")
        print(f"  - Actual keys: {actual_keys}")

        assert actual_keys == required_keys, f"Contract mismatch: {actual_keys} != {required_keys}"

        # Verify no extra fields
        extra_keys = actual_keys - required_keys
        assert len(extra_keys) == 0, f"Extra fields not allowed: {extra_keys}"

        # Verify types
        assert isinstance(page_data["url"], str)
        assert isinstance(page_data["title"], str)
        assert isinstance(page_data["platform"], str)
        assert isinstance(page_data["forms"], list)
        assert isinstance(page_data["fields"], list)
        assert isinstance(page_data["buttons"], list)
        assert isinstance(page_data["links"], list)
        assert isinstance(page_data["page_type"], str)
        assert isinstance(page_data["metadata"], dict)

        print("✅ Page data contract verified (strict structure)")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("PAGE DATA PRODUCER VALIDATION")
    print("HTML → page_data → PageAnalyzer → ExecutionPlanner")
    print("="*70)

    results = {}

    results["linkedin_extraction"] = test_linkedin_html_to_page_data()
    results["indeed_extraction"] = test_indeed_html_to_page_data()
    results["naukri_extraction"] = test_naukri_html_to_page_data()
    results["page_data_to_analyzer"] = test_page_data_to_analyzer()
    results["contract_validation"] = test_page_data_contract()

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
        print("✅ PAGE DATA PRODUCER LAYER COMPLETE")
        print("="*70)
        print("\nCapabilities validated:")
        print("  ✅ HTML extraction (LinkedIn, Indeed, Naukri)")
        print("  ✅ Strict page_data contract enforced")
        print("  ✅ Platform-specific page type detection")
        print("  ✅ Integration with PageAnalyzer")
        print("  ✅ Integration with ExecutionPlanner")
        print("\nBrowser-independent extraction complete.")
        print("Ready for browser automation integration (Phase 4+)")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

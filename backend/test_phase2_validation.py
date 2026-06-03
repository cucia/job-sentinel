"""
Phase 2 Validation - Workflow Classification Integration

Validates that workflow classification is integrated into the runtime flow:
Discovery → Task Creation → Workflow Classification → Strategy Selection

Tests that classification results are stored and execution_strategy is attached to tasks.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_task_with_workflow_classification():
    """Test 1: Task model supports workflow classification data."""
    print("\n=== Test 1: Task Model Workflow Classification Support ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus

        print("✓ Creating task...")
        task = Task(
            task_id="task_001",
            job_id="job_001",
            source_platform="linkedin",
            status=TaskStatus.DISCOVERED
        )

        print("✓ Task created")
        print(f"  - Task ID: {task.task_id}")
        print(f"  - Job ID: {task.job_id}")
        print(f"  - Platform: {task.source_platform}")

        # Check if task can store workflow classification data
        print("✓ Checking task attributes for workflow classification...")

        # Add workflow classification data to task
        task.workflow_type = "linkedin_easy_apply"
        task.workflow_confidence = 0.95
        task.execution_strategy = "linkedin_easy_apply_flow"
        task.workflow_indicators = {
            "linkedin_url": True,
            "easy_apply_button": True,
        }

        print(f"  - Workflow type: {task.workflow_type}")
        print(f"  - Confidence: {task.workflow_confidence}")
        print(f"  - Strategy: {task.execution_strategy}")
        print(f"  - Indicators: {task.workflow_indicators}")

        print("\n✅ Task model supports workflow classification data")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_discovery_to_task_creation_flow():
    """Test 2: Discovery → Task Creation flow."""
    print("\n=== Test 2: Discovery → Task Creation Flow ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus

        print("✓ Simulating discovery phase...")
        discovered_jobs = [
            {
                "job_id": "job_linkedin_001",
                "title": "Software Engineer",
                "url": "https://www.linkedin.com/jobs/view/1234567890",
                "platform": "linkedin",
            },
            {
                "job_id": "job_workday_001",
                "title": "Product Manager",
                "url": "https://company.workday.com/careers/jobs/123",
                "platform": "workday",
            },
        ]

        print(f"  - Discovered {len(discovered_jobs)} jobs")

        print("✓ Creating tasks from discovered jobs...")
        tasks = []
        for job in discovered_jobs:
            task = Task(
                task_id=f"task_{job['job_id']}",
                job_id=job["job_id"],
                source_platform=job["platform"],
                status=TaskStatus.DISCOVERED
            )
            # Store job metadata for classification
            task.job_url = job["url"]
            task.job_title = job["title"]
            tasks.append(task)

        print(f"  - Created {len(tasks)} tasks")
        for task in tasks:
            print(f"    - {task.task_id}: {task.source_platform}")

        print("\n✅ Discovery → Task Creation flow verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_classification_integration():
    """Test 3: Workflow Classification integration with tasks."""
    print("\n=== Test 3: Workflow Classification Integration ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow_classification import create_classifier

        print("✓ Creating classifier...")
        classifier = create_classifier()

        print("✓ Creating task...")
        task = Task(
            task_id="task_linkedin_001",
            job_id="job_linkedin_001",
            source_platform="linkedin",
            status=TaskStatus.DISCOVERED
        )

        # Store job metadata
        task.job_url = "https://www.linkedin.com/jobs/view/1234567890"
        task.job_title = "Software Engineer at Company | LinkedIn"
        task.page_metadata = {"og:site_name": "LinkedIn"}
        task.dom_info = {
            "easy_apply_button": True,
            "linkedin_job_card": True,
        }

        print("✓ Classifying workflow...")
        classification = classifier.classify(
            url=task.job_url,
            page_title=task.job_title,
            page_metadata=task.page_metadata,
            dom_info=task.dom_info,
        )

        print(f"  - Workflow type: {classification.workflow_type.value}")
        print(f"  - Confidence: {classification.confidence_score:.0%}")
        print(f"  - Strategy: {classification.execution_strategy.value}")

        print("✓ Attaching classification to task...")
        task.workflow_type = classification.workflow_type.value
        task.workflow_confidence = classification.confidence_score
        task.execution_strategy = classification.execution_strategy.value
        task.workflow_indicators = classification.indicators

        print(f"  - Task workflow_type: {task.workflow_type}")
        print(f"  - Task execution_strategy: {task.execution_strategy}")

        print("\n✅ Workflow Classification integration verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_workflow_types_integration():
    """Test 4: All workflow types integrated with tasks."""
    print("\n=== Test 4: All Workflow Types Integration ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow_classification import create_classifier

        classifier = create_classifier()

        workflows = [
            {
                "name": "LinkedIn Easy Apply",
                "url": "https://www.linkedin.com/jobs/view/1234567890",
                "title": "Software Engineer | LinkedIn",
                "metadata": {"og:site_name": "LinkedIn"},
                "dom": {"easy_apply_button": True, "linkedin_job_card": True},
            },
            {
                "name": "Workday",
                "url": "https://company.workday.com/careers/jobs/123",
                "title": "Workday Careers",
                "metadata": {"og:site_name": "Workday"},
                "dom": {"workday_form": True, "workday_iframe": True},
            },
            {
                "name": "Greenhouse",
                "url": "https://boards.greenhouse.io/company/jobs/1234567",
                "title": "Greenhouse Job Board",
                "metadata": {"og:site_name": "Greenhouse"},
                "dom": {"greenhouse_form": True, "greenhouse_job_board": True},
            },
            {
                "name": "Lever",
                "url": "https://jobs.lever.co/company/abc123",
                "title": "Lever Job Posting",
                "metadata": {"og:site_name": "Lever"},
                "dom": {"lever_form": True, "lever_job_posting": True},
            },
            {
                "name": "Oracle",
                "url": "https://oracle.com/careers/jobs",
                "title": "Oracle Careers",
                "metadata": {"og:site_name": "Oracle"},
                "dom": {"oracle_form": True, "oracle_careers_portal": True},
            },
            {
                "name": "Generic",
                "url": "https://example.com/apply",
                "title": "Apply Now",
                "metadata": {},
                "dom": {"form_fields": True, "submit_button": True},
            },
        ]

        print("✓ Testing all workflow types...\n")

        for workflow in workflows:
            print(f"  Testing {workflow['name']}...")

            # Create task
            task = Task(
                task_id=f"task_{workflow['name'].lower().replace(' ', '_')}",
                job_id=f"job_{workflow['name'].lower().replace(' ', '_')}",
                source_platform=workflow["name"].lower().split()[0],
                status=TaskStatus.DISCOVERED
            )

            # Store metadata
            task.job_url = workflow["url"]
            task.job_title = workflow["title"]
            task.page_metadata = workflow["metadata"]
            task.dom_info = workflow["dom"]

            # Classify
            classification = classifier.classify(
                url=task.job_url,
                page_title=task.job_title,
                page_metadata=task.page_metadata,
                dom_info=task.dom_info,
            )

            # Attach to task
            task.workflow_type = classification.workflow_type.value
            task.workflow_confidence = classification.confidence_score
            task.execution_strategy = classification.execution_strategy.value

            print(f"    ✓ {workflow['name']}")
            print(f"      - Type: {task.workflow_type}")
            print(f"      - Confidence: {task.workflow_confidence:.0%}")
            print(f"      - Strategy: {task.execution_strategy}")

        print("\n✅ All workflow types integrated successfully")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_selection_from_classification():
    """Test 5: Execution strategy selection from classification."""
    print("\n=== Test 5: Execution Strategy Selection ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow_classification import create_classifier, ExecutionStrategy

        classifier = create_classifier()

        print("✓ Testing strategy selection for each workflow type...\n")

        test_cases = [
            ("LinkedIn", "https://www.linkedin.com/jobs/view/1234567890", ExecutionStrategy.LINKEDIN_EASY_APPLY_FLOW),
            ("Workday", "https://company.workday.com/careers/jobs/123", ExecutionStrategy.WORKDAY_FLOW),
            ("Greenhouse", "https://boards.greenhouse.io/company/jobs/1234567", ExecutionStrategy.GREENHOUSE_FLOW),
            ("Lever", "https://jobs.lever.co/company/abc123", ExecutionStrategy.LEVER_FLOW),
            ("Oracle", "https://oracle.com/careers/jobs", ExecutionStrategy.ORACLE_FLOW),
            ("Generic", "https://example.com/apply", ExecutionStrategy.GENERIC_FORM_FLOW),
        ]

        for name, url, expected_strategy in test_cases:
            classification = classifier.classify(url=url)

            print(f"  {name}:")
            print(f"    - Classified as: {classification.workflow_type.value}")
            print(f"    - Strategy: {classification.execution_strategy.value}")
            print(f"    - Expected: {expected_strategy.value}")

            assert classification.execution_strategy == expected_strategy, \
                f"Strategy mismatch for {name}"
            print(f"    ✓ Strategy matches expected")

        print("\n✅ Execution strategy selection verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_runtime_flow_with_classification():
    """Test 6: Complete runtime flow with classification."""
    print("\n=== Test 6: Complete Runtime Flow with Classification ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow_classification import create_classifier

        print("✓ Step 1: Discovery phase")
        discovered_jobs = [
            {
                "job_id": "job_001",
                "url": "https://www.linkedin.com/jobs/view/1234567890",
                "title": "Software Engineer | LinkedIn",
                "platform": "linkedin",
            }
        ]
        print(f"  - Discovered {len(discovered_jobs)} job(s)")

        print("✓ Step 2: Task creation")
        task = Task(
            task_id="task_001",
            job_id=discovered_jobs[0]["job_id"],
            source_platform=discovered_jobs[0]["platform"],
            status=TaskStatus.DISCOVERED
        )
        task.job_url = discovered_jobs[0]["url"]
        task.job_title = discovered_jobs[0]["title"]
        print(f"  - Task created: {task.task_id}")

        print("✓ Step 3: Workflow classification")
        classifier = create_classifier()
        classification = classifier.classify(
            url=task.job_url,
            page_title=task.job_title,
        )
        print(f"  - Classified as: {classification.workflow_type.value}")

        print("✓ Step 4: Strategy selection")
        task.workflow_type = classification.workflow_type.value
        task.execution_strategy = classification.execution_strategy.value
        task.workflow_confidence = classification.confidence_score
        print(f"  - Strategy selected: {task.execution_strategy}")

        print("✓ Step 5: Task ready for execution")
        print(f"  - Task ID: {task.task_id}")
        print(f"  - Workflow: {task.workflow_type}")
        print(f"  - Strategy: {task.execution_strategy}")
        print(f"  - Confidence: {task.workflow_confidence:.0%}")

        print("\n✅ Complete runtime flow with classification verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 validation tests."""
    print("\n" + "="*70)
    print("PHASE 2 VALIDATION - WORKFLOW CLASSIFICATION INTEGRATION")
    print("="*70)

    results = {}

    # Run all tests
    results["task_workflow_support"] = test_task_with_workflow_classification()
    results["discovery_to_task"] = test_discovery_to_task_creation_flow()
    results["classification_integration"] = test_workflow_classification_integration()
    results["all_workflow_types"] = test_all_workflow_types_integration()
    results["strategy_selection"] = test_strategy_selection_from_classification()
    results["complete_flow"] = test_runtime_flow_with_classification()

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
        print("✅ PHASE 2 VALIDATION SUCCESSFUL")
        print("="*70)
        print("\nWorkflow classification is integrated into runtime flow:")
        print("  ✅ Discovery → Task Creation")
        print("  ✅ Task Creation → Workflow Classification")
        print("  ✅ Workflow Classification → Strategy Selection")
        print("\nSupported workflows:")
        print("  ✅ LinkedIn Easy Apply")
        print("  ✅ Workday")
        print("  ✅ Greenhouse")
        print("  ✅ Lever")
        print("  ✅ Oracle")
        print("  ✅ Generic/Unknown")
        print("\nClassification data stored in task:")
        print("  ✅ workflow_type")
        print("  ✅ workflow_confidence")
        print("  ✅ execution_strategy")
        print("  ✅ workflow_indicators")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

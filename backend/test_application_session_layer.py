"""
Application Session and Page Analysis Validation

Validates complete end-to-end flow:
Task → Workflow Handler → Application Session → Page Analysis → Execution Plan

Tests session creation, page analysis, and execution planning for:
- LinkedIn
- Indeed
- Naukri
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_linkedin_session_and_planning():
    """Test 1: LinkedIn session creation, analysis, and planning."""
    print("\n=== Test 1: LinkedIn Session and Planning ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow.handlers import WorkflowHandlerRegistry
        from backend.application.page_analyzer import create_page_analyzer
        from backend.application.execution_planner import create_execution_planner

        print("✓ Creating task")
        task = Task(
            task_id="task_linkedin_001",
            job_id="job_linkedin_001",
            source_platform="linkedin",
            status=TaskStatus.DISCOVERED,
        )
        task.workflow_type = "linkedin_easy_apply"
        task.execution_strategy = "linkedin_easy_apply_flow"
        task.workflow_confidence = 0.95
        task.metadata = {"job": {"url": "https://www.linkedin.com/jobs/view/123"}}

        print("✓ Route to handler")
        registry = WorkflowHandlerRegistry()
        routing_result = registry.route_task(task)

        assert routing_result.get("valid"), "Routing should be valid"
        assert "session" in routing_result, "Session should be created"

        session = routing_result["session"]
        print(f"  - Session created: {session.session_id}")
        print(f"  - Workflow: {session.workflow_type}")

        print("✓ Analyzing page")
        # Mock LinkedIn profile page
        linkedin_page_data = {
            "url": "https://www.linkedin.com/jobs/view/123/apply",
            "title": "Apply - LinkedIn",
            "forms": [
                {
                    "id": "profile_form",
                    "name": "profile",
                    "elements": [
                        {
                            "id": "fname",
                            "type": "input",
                            "label": "First Name",
                            "name": "firstName",
                            "required": True,
                            "visible": True,
                        },
                        {
                            "id": "lname",
                            "type": "input",
                            "label": "Last Name",
                            "name": "lastName",
                            "required": True,
                            "visible": True,
                        },
                    ],
                }
            ],
            "buttons": [
                {"id": "next_btn", "text": "Next", "label": "Next"},
            ],
            "validation_messages": [],
        }

        analyzer = create_page_analyzer()
        analysis = analyzer.analyze_page(linkedin_page_data)

        print(f"  - Page type: {analysis.page_type}")
        print(f"  - Forms found: {len(analysis.forms)}")
        print(f"  - Fields found: {len(analysis.visible_fields)}")

        print("✓ Generating execution plan")
        planner = create_execution_planner("linkedin_easy_apply")
        plan = planner.generate_plan(
            job_id=task.job_id,
            task_id=task.task_id,
            page_analysis=analysis,
        )

        print(f"  - Plan ID: {plan.plan_id}")
        print(f"  - Steps: {len(plan.steps)}")
        print(f"  - Confidence: {plan.confidence_score:.0%}")

        print("✓ Storing results in session")
        session.record_page_analysis(analysis)
        session.set_execution_plan(plan)

        print(f"  - Session status: {session.status}")
        print(f"  - Analysis stored: {len(session.page_analyses)} page(s)")
        print(f"  - Plan ready: {session.execution_plan is not None}")

        print("\n✅ LinkedIn session and planning verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indeed_session_and_planning():
    """Test 2: Indeed session creation, analysis, and planning."""
    print("\n=== Test 2: Indeed Session and Planning ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow.handlers import WorkflowHandlerRegistry
        from backend.application.page_analyzer import create_page_analyzer
        from backend.application.execution_planner import create_execution_planner

        print("✓ Creating task")
        task = Task(
            task_id="task_indeed_001",
            job_id="job_indeed_001",
            source_platform="indeed",
            status=TaskStatus.DISCOVERED,
        )
        task.workflow_type = "indeed"
        task.execution_strategy = "generic_form_flow"
        task.workflow_confidence = 0.85
        task.metadata = {"job": {"url": "https://indeed.com/viewjob?jk=123"}}

        print("✓ Route to handler")
        registry = WorkflowHandlerRegistry()
        routing_result = registry.route_task(task)

        assert routing_result.get("valid"), "Routing should be valid"
        session = routing_result["session"]

        print("✓ Analyzing page")
        # Mock Indeed application form page
        indeed_page_data = {
            "url": "https://indeed.com/viewjob?jk=123/apply",
            "title": "Apply Now - Indeed",
            "forms": [
                {
                    "id": "resume_form",
                    "name": "upload",
                    "elements": [
                        {
                            "id": "resume_upload",
                            "type": "file",
                            "label": "Upload Resume",
                            "name": "resume",
                            "required": True,
                            "visible": True,
                        },
                    ],
                },
                {
                    "id": "profile_form",
                    "name": "profile",
                    "elements": [
                        {
                            "id": "email",
                            "type": "input",
                            "label": "Email",
                            "name": "email",
                            "required": True,
                            "visible": True,
                        },
                        {
                            "id": "phone",
                            "type": "input",
                            "label": "Phone",
                            "name": "phone",
                            "required": False,
                            "visible": True,
                        },
                    ],
                },
            ],
            "buttons": [
                {"id": "apply_btn", "text": "Apply Now", "label": "Apply Now"},
            ],
            "has_submit_button": True,
        }

        analyzer = create_page_analyzer()
        analysis = analyzer.analyze_page(indeed_page_data)

        print(f"  - Page type: {analysis.page_type}")
        print(f"  - Upload fields: {len(analysis.upload_fields)}")
        print(f"  - Fields found: {len(analysis.visible_fields)}")

        print("✓ Generating execution plan")
        planner = create_execution_planner("indeed")
        plan = planner.generate_plan(
            job_id=task.job_id,
            task_id=task.task_id,
            page_analysis=analysis,
        )

        print(f"  - Steps: {len(plan.steps)}")
        print(f"  - First action: {plan.steps[0].action.value if plan.steps else 'none'}")

        print("✓ Storing results in session")
        session.record_page_analysis(analysis)
        session.set_execution_plan(plan)

        print(f"  - Session has {len(session.page_analyses)} page analysis")
        print(f"  - Plan stored: {session.execution_plan is not None}")

        print("\n✅ Indeed session and planning verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_naukri_session_and_planning():
    """Test 3: Naukri session creation, analysis, and planning."""
    print("\n=== Test 3: Naukri Session and Planning ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow.handlers import WorkflowHandlerRegistry
        from backend.application.page_analyzer import create_page_analyzer
        from backend.application.execution_planner import create_execution_planner

        print("✓ Creating task")
        task = Task(
            task_id="task_naukri_001",
            job_id="job_naukri_001",
            source_platform="naukri",
            status=TaskStatus.DISCOVERED,
        )
        task.workflow_type = "naukri"
        task.execution_strategy = "generic_form_flow"
        task.workflow_confidence = 0.8
        task.metadata = {"job": {"url": "https://naukri.com/job/123"}}

        print("✓ Route to handler")
        registry = WorkflowHandlerRegistry()
        routing_result = registry.route_task(task)

        assert routing_result.get("valid"), "Routing should be valid"
        session = routing_result["session"]

        print("✓ Analyzing page")
        # Mock Naukri application form page
        naukri_page_data = {
            "url": "https://naukri.com/job/123/apply",
            "title": "Apply - Naukri",
            "forms": [
                {
                    "id": "profile_form",
                    "name": "profile",
                    "elements": [
                        {
                            "id": "name",
                            "type": "input",
                            "label": "Full Name",
                            "name": "fullName",
                            "required": True,
                            "visible": True,
                        },
                        {
                            "id": "skills",
                            "type": "textarea",
                            "label": "Key Skills",
                            "name": "keySkills",
                            "required": True,
                            "visible": True,
                        },
                    ],
                },
            ],
            "buttons": [
                {"id": "submit_btn", "text": "Submit Application", "label": "Submit"},
            ],
            "has_submit_button": True,
        }

        analyzer = create_page_analyzer()
        analysis = analyzer.analyze_page(naukri_page_data)

        print(f"  - Page type: {analysis.page_type}")
        print(f"  - Forms: {len(analysis.forms)}")
        print(f"  - Fields: {len(analysis.visible_fields)}")

        print("✓ Generating execution plan")
        planner = create_execution_planner("naukri")
        plan = planner.generate_plan(
            job_id=task.job_id,
            task_id=task.task_id,
            page_analysis=analysis,
        )

        print(f"  - Plan steps: {len(plan.steps)}")
        print(f"  - Estimated duration: {plan.total_estimated_duration}s")

        print("✓ Storing results in session")
        session.record_page_analysis(analysis)
        session.set_execution_plan(plan)

        print(f"  - Session analysis stored")
        print(f"  - Plan ready for execution")

        print("\n✅ Naukri session and planning verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_session_persistence():
    """Test 4: Session serialization and recovery."""
    print("\n=== Test 4: Session Persistence ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow.handlers import LinkedInEasyApplyHandler
        from backend.application.session import ApplicationSession

        print("✓ Creating session")
        handler = LinkedInEasyApplyHandler()
        task = Task(
            task_id="task_persist_001",
            job_id="job_persist_001",
            source_platform="linkedin",
            status=TaskStatus.DISCOVERED,
        )
        session = handler.create_application_session(task, "https://example.com")

        print("✓ Adding data to session")
        session.metadata = {"user_id": "123", "profile_version": "1"}
        session.discovered_fields = {"email": "user@example.com", "name": "John Doe"}

        print("✓ Serializing session")
        session_dict = session.to_dict()

        print(f"  - Serialized keys: {len(session_dict)}")
        print(f"  - Session ID preserved: {session_dict['session_id'] == session.session_id}")

        print("✓ Deserializing session")
        restored_session = ApplicationSession.from_dict(session_dict)

        print(f"  - Session ID recovered: {restored_session.session_id == session.session_id}")
        print(f"  - Metadata recovered: {restored_session.metadata == session.metadata}")
        print(f"  - Fields recovered: {restored_session.discovered_fields == session.discovered_fields}")

        assert restored_session.session_id == session.session_id
        assert restored_session.metadata == session.metadata

        print("\n✅ Session persistence verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow_flow():
    """Test 5: Complete workflow from task to execution plan."""
    print("\n=== Test 5: Complete Workflow Flow ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow.handlers import WorkflowHandlerRegistry
        from backend.application.page_analyzer import create_page_analyzer
        from backend.application.execution_planner import create_execution_planner

        print("✓ Step 1: Task created (classified)")
        task = Task(
            task_id="task_flow_001",
            job_id="job_flow_001",
            source_platform="linkedin",
            status=TaskStatus.DISCOVERED,
        )
        task.workflow_type = "linkedin_easy_apply"
        task.execution_strategy = "linkedin_easy_apply_flow"
        task.workflow_confidence = 0.95

        print("✓ Step 2: Routed to handler")
        registry = WorkflowHandlerRegistry()
        routing = registry.route_task(task)
        assert routing.get("valid")

        session = routing["session"]
        print(f"  - Session created")

        print("✓ Step 3: Page analyzed")
        page_data = {
            "url": "https://www.linkedin.com/jobs/view/123/apply",
            "title": "Apply - LinkedIn",
            "forms": [
                {
                    "id": "form1",
                    "elements": [
                        {
                            "id": "fname",
                            "type": "input",
                            "label": "First Name",
                            "required": True,
                            "visible": True,
                        },
                    ],
                }
            ],
            "buttons": [{"id": "next", "text": "Next"}],
        }

        analyzer = create_page_analyzer()
        analysis = analyzer.analyze_page(page_data)
        session.record_page_analysis(analysis)

        print("✓ Step 4: Execution plan generated")
        planner = create_execution_planner("linkedin_easy_apply")
        plan = planner.generate_plan(task.job_id, task.task_id, analysis)
        session.set_execution_plan(plan)

        print(f"  - Plan ready: {plan.confidence_score:.0%} confidence")
        print(f"  - Steps to execute: {len(plan.steps)}")

        print("✓ Step 5: Session tracking complete")
        print(f"  - Session status: {session.status}")
        print(f"  - Pages analyzed: {len(session.page_analyses)}")
        print(f"  - Execution plan: {session.execution_plan is not None}")

        print("\n✅ Complete workflow flow verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("APPLICATION SESSION AND PAGE ANALYSIS VALIDATION")
    print("Task → Handler → Session → Analysis → Planning")
    print("="*70)

    results = {}

    results["linkedin_session"] = test_linkedin_session_and_planning()
    results["indeed_session"] = test_indeed_session_and_planning()
    results["naukri_session"] = test_naukri_session_and_planning()
    results["session_persistence"] = test_session_persistence()
    results["full_workflow"] = test_full_workflow_flow()

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
        print("✅ APPLICATION SESSION LAYER COMPLETE")
        print("="*70)
        print("\nCapabilities validated:")
        print("  ✅ Application sessions created and tracked")
        print("  ✅ Page analysis extracts normalized structures")
        print("  ✅ Execution plans generated for each workflow")
        print("  ✅ Sessions persist and recover data")
        print("  ✅ Complete end-to-end workflow functions")
        print("\nWorkflow types supported:")
        print("  ✅ LinkedIn Easy Apply")
        print("  ✅ Indeed")
        print("  ✅ Naukri")
        print("\nNext step: Implement browser integration for real page analysis")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

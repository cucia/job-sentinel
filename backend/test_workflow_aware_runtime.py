"""
End-to-End Workflow-Aware Runtime Validation

Validates complete flow:
Discovery → Classification → Task Enrichment → Queue → Orchestrator → Workflow Routing

Tests that workflow_type and execution_strategy are preserved and used correctly.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_discovery_to_workflow_routing():
    """Test complete flow from discovery through workflow routing."""
    print("\n=== Test 1: Discovery → Classification → Routing ===\n")

    try:
        from backend.workflow_classification import create_classifier
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow.handlers import WorkflowHandlerRegistry

        print("✓ Step 1: Simulate job discovery")
        job = {
            "job_id": "job_001",
            "url": "https://www.linkedin.com/jobs/view/1234567890",
            "title": "Software Engineer | LinkedIn",
            "platform": "linkedin",
        }
        print(f"  - Discovered: {job['title']}")

        print("✓ Step 2: Classify workflow")
        classifier = create_classifier()
        classification = classifier.classify(url=job["url"], page_title=job["title"])
        print(f"  - Type: {classification.workflow_type.value}")
        print(f"  - Strategy: {classification.execution_strategy.value}")
        print(f"  - Confidence: {classification.confidence_score:.0%}")

        print("✓ Step 3: Create task with classification")
        task = Task(
            task_id="task_001",
            job_id=job["job_id"],
            source_platform=job["platform"],
            status=TaskStatus.DISCOVERED,
        )
        task.workflow_type = classification.workflow_type.value
        task.execution_strategy = classification.execution_strategy.value
        task.workflow_confidence = classification.confidence_score
        task.workflow_indicators = classification.indicators
        print(f"  - Task created with workflow data")

        print("✓ Step 4: Route to workflow handler")
        registry = WorkflowHandlerRegistry()
        routing_result = registry.route_task(task)

        print(f"  - Handler: {routing_result.get('handler')}")
        print(f"  - Valid: {routing_result.get('valid')}")
        print(f"  - Next step: {routing_result.get('next_step')}")

        assert routing_result.get("valid"), "Routing should be valid"
        assert routing_result.get("handler") == "LinkedInEasyApplyHandler"

        print("\n✅ Complete flow verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_workflows_end_to_end():
    """Test all 6 workflow types through complete flow."""
    print("\n=== Test 2: All Workflow Types End-to-End ===\n")

    try:
        from backend.workflow_classification import create_classifier
        from backend.runtime.task_model import Task, TaskStatus
        from backend.workflow.handlers import WorkflowHandlerRegistry

        classifier = create_classifier()
        registry = WorkflowHandlerRegistry()

        workflows = [
            {
                "name": "LinkedIn Easy Apply",
                "url": "https://www.linkedin.com/jobs/view/1234567890",
                "platform": "linkedin",
                "expected_type": "linkedin_easy_apply",
                "expected_handler": "LinkedInEasyApplyHandler",
            },
            {
                "name": "Workday",
                "url": "https://company.workday.com/careers/jobs/123",
                "platform": "workday",
                "expected_type": "workday",
                "expected_handler": "WorkdayHandler",
            },
            {
                "name": "Greenhouse",
                "url": "https://boards.greenhouse.io/company/jobs/1234567",
                "platform": "greenhouse",
                "expected_type": "greenhouse",
                "expected_handler": "GreenhouseHandler",
            },
            {
                "name": "Lever",
                "url": "https://jobs.lever.co/company/abc123",
                "platform": "lever",
                "expected_type": "lever",
                "expected_handler": "LeverHandler",
            },
            {
                "name": "Oracle",
                "url": "https://oracle.com/careers/jobs",
                "platform": "oracle",
                "expected_type": "oracle",
                "expected_handler": "OracleHandler",
            },
            {
                "name": "Generic",
                "url": "https://example.com/apply",
                "platform": "generic",
                "expected_type": "generic",
                "expected_handler": "GenericHandler",
            },
        ]

        print("Testing end-to-end flow for all workflow types:\n")

        for workflow in workflows:
            print(f"  Testing {workflow['name']}...")

            # Classify
            classification = classifier.classify(url=workflow["url"])

            # Create task
            task = Task(
                task_id=f"task_{workflow['platform']}",
                job_id=f"job_{workflow['platform']}",
                source_platform=workflow["platform"],
                status=TaskStatus.DISCOVERED,
            )
            task.workflow_type = classification.workflow_type.value
            task.execution_strategy = classification.execution_strategy.value
            task.workflow_confidence = classification.confidence_score

            # Route
            routing_result = registry.route_task(task)

            # Verify
            assert routing_result.get("valid"), f"Routing should be valid for {workflow['name']}"
            assert routing_result.get("handler") == workflow["expected_handler"], \
                f"Handler mismatch for {workflow['name']}"

            print(f"    ✓ {workflow['name']}")
            print(f"      - Type: {task.workflow_type}")
            print(f"      - Strategy: {task.execution_strategy}")
            print(f"      - Handler: {routing_result.get('handler')}")
            print(f"      - Next step: {routing_result.get('next_step')}")

        print("\n✅ All workflow types end-to-end verified")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_data_through_queue():
    """Test that workflow data survives queue operations."""
    print("\n=== Test 3: Workflow Data Through Queue ===\n")

    try:
        from backend.workflow_classification import create_classifier
        from backend.runtime.task_model import Task, TaskStatus
        from backend.queue.queue import Queue
        from backend.persistence.task_storage import TaskStorage
        import tempfile

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            print("✓ Creating task with classification data")
            classifier = create_classifier()
            classification = classifier.classify(
                url="https://www.linkedin.com/jobs/view/1234567890"
            )

            task = Task(
                task_id="task_queue_001",
                job_id="job_queue_001",
                source_platform="linkedin",
                status=TaskStatus.DISCOVERED,
            )
            task.workflow_type = classification.workflow_type.value
            task.execution_strategy = classification.execution_strategy.value
            task.workflow_confidence = classification.confidence_score
            task.workflow_indicators = classification.indicators

            print("✓ Enqueueing task")
            storage = TaskStorage(db_path)
            queue = Queue(storage)
            queue.enqueue(task)

            print("✓ Dequeueing task")
            dequeued_tasks = queue.dequeue(limit=1)
            assert len(dequeued_tasks) > 0, "Should dequeue task"

            dequeued = dequeued_tasks[0]

            print("✓ Verifying workflow data survived queue")
            assert dequeued.workflow_type == task.workflow_type, "workflow_type lost"
            assert dequeued.execution_strategy == task.execution_strategy, "execution_strategy lost"
            assert dequeued.workflow_confidence == task.workflow_confidence, "confidence lost"

            print(f"  - workflow_type preserved: {dequeued.workflow_type}")
            print(f"  - execution_strategy preserved: {dequeued.execution_strategy}")
            print(f"  - confidence preserved: {dequeued.workflow_confidence:.0%}")

            print("\n✅ Workflow data survives queue operations")
            return True

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_workflow_routing():
    """Test orchestrator workflow routing."""
    print("\n=== Test 4: Orchestrator Workflow Routing ===\n")

    try:
        from backend.workflow_classification import create_classifier
        from backend.runtime.task_model import Task, TaskStatus
        from backend.orchestrator.orchestrator import RuntimeOrchestrator
        from backend.queue.queue import Queue
        from backend.state.state_manager import StateManager
        from backend.workers.browser_worker import WorkerPool
        from backend.manual_review.review_queue import ManualReviewQueue
        from backend.persistence.task_storage import TaskStorage
        from backend.events.event_bus import EventBus
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            print("✓ Setting up orchestrator")
            storage = TaskStorage(db_path)
            event_bus = EventBus()
            queue = Queue(storage)
            state_manager = StateManager(storage, event_bus)
            manual_review_queue = ManualReviewQueue(storage)
            worker_pool = WorkerPool()

            orchestrator = RuntimeOrchestrator(
                queue=queue,
                state_manager=state_manager,
                worker_pool=worker_pool,
                manual_review_queue=manual_review_queue,
            )

            print("✓ Creating classified task")
            classifier = create_classifier()
            classification = classifier.classify(
                url="https://boards.greenhouse.io/company/jobs/1234567"
            )

            task = Task(
                task_id="task_orch_001",
                job_id="job_orch_001",
                source_platform="greenhouse",
                status=TaskStatus.DISCOVERED,
            )
            task.workflow_type = classification.workflow_type.value
            task.execution_strategy = classification.execution_strategy.value
            task.workflow_confidence = classification.confidence_score

            print("✓ Orchestrator routing task")
            routing_result = orchestrator._route_to_workflow(task)

            print(f"  - Valid: {routing_result.get('valid')}")
            print(f"  - Handler: {routing_result.get('handler')}")
            print(f"  - Next step: {routing_result.get('next_step')}")

            assert routing_result.get("valid"), "Routing should be valid"
            assert routing_result.get("handler") == "GreenhouseHandler"

            print("\n✅ Orchestrator workflow routing verified")
            return True

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all end-to-end validation tests."""
    print("\n" + "="*70)
    print("END-TO-END WORKFLOW-AWARE RUNTIME VALIDATION")
    print("Discovery → Classification → Routing → Handler")
    print("="*70)

    results = {}

    results["complete_flow"] = test_discovery_to_workflow_routing()
    results["all_workflows"] = test_all_workflows_end_to_end()
    results["queue_preservation"] = test_workflow_data_through_queue()
    results["orchestrator_routing"] = test_orchestrator_workflow_routing()

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
        print("✅ WORKFLOW-AWARE RUNTIME COMPLETE")
        print("="*70)
        print("\nRuntime is fully workflow-aware:")
        print("  ✅ Jobs classified during discovery")
        print("  ✅ workflow_type attached to tasks")
        print("  ✅ execution_strategy attached to tasks")
        print("  ✅ Classification data survives queue")
        print("  ✅ Orchestrator routes by workflow type")
        print("  ✅ All 6 workflows supported")
        print("\nExecution path:")
        print("  Job (discovered)")
        print("    ↓")
        print("  Classification (workflow_type, strategy identified)")
        print("    ↓")
        print("  Task Enrichment (data attached)")
        print("    ↓")
        print("  Queue (data preserved)")
        print("    ↓")
        print("  Orchestrator (routes by workflow_type)")
        print("    ↓")
        print("  Workflow Handler (receives routed task)")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

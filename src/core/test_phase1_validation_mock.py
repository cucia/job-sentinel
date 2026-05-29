"""
Phase 1.5 Runtime Validation - Mock-Based Test Suite

Validates the runtime backbone without external dependencies.
Uses mocking to isolate Phase 1 components from platform integrations.
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_imports_with_mocking():
    """Test 1: Validate imports with mocked dependencies."""
    print("\n=== Test 1: Import Validation (with mocking) ===\n")

    try:
        # Mock platform collectors before importing discovery
        with patch("src.platforms.linkedin.collector.collect_jobs", return_value=[]), \
             patch("src.platforms.indeed.collector.collect_jobs", return_value=[]), \
             patch("src.platforms.naukri.collector.collect_jobs", return_value=[]):

            print("✓ Importing scheduler...")
            from src.core.scheduler import RuntimeScheduler, create_scheduler

            print("✓ Importing discovery...")
            from src.discovery import JobDiscovery, create_discovery

            print("✓ Importing execution pipeline...")
            from backend.execution_pipeline import ExecutionPipeline

            print("✓ Importing runtime bridge...")
            from backend.bridge import create_runtime_bridge

            print("✓ Importing orchestrator...")
            from backend.orchestrator.orchestrator import RuntimeOrchestrator

            print("✓ Importing queue...")
            from backend.queue.queue import TaskQueue

            print("✓ Importing state manager...")
            from backend.state.state_manager import StateManager

            print("✓ Importing event bus...")
            from backend.events.event_bus import EventBus

            print("✓ Importing task model...")
            from backend.runtime.task_model import Task

            print("✓ Importing workers...")
            from backend.workers.browser_worker import BrowserWorker

            print("✓ Importing storage...")
            from src.core.storage import init_db, get_model_state

            print("✓ Importing config...")
            from src.core.config import load_settings, load_profile

            print("\n✅ All imports successful - No circular dependencies detected")
            return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test 2: Validate configuration loads correctly."""
    print("\n=== Test 2: Configuration Validation ===\n")

    try:
        from src.core.config import load_settings, load_profile

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        print(f"✓ Loading settings from {base_dir}...")
        settings = load_settings(base_dir)
        assert settings is not None, "Settings is None"
        assert "app" in settings, "Missing 'app' section"
        assert "platforms" in settings, "Missing 'platforms' section"
        print(f"  - App config: {settings.get('app', {}).get('run_interval_seconds', 'N/A')}s interval")
        print(f"  - Platforms: {settings.get('platforms', {}).get('enabled', [])}")

        print(f"✓ Loading profile from {base_dir}...")
        profile = load_profile(base_dir)
        assert profile is not None, "Profile is None"
        assert "name" in profile, "Missing 'name' in profile"
        print(f"  - Profile: {profile.get('name', 'N/A')}")

        print("\n✅ Configuration loaded successfully")
        return True, settings, profile, base_dir

    except Exception as e:
        print(f"\n❌ Configuration failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None, None


def test_initialization(settings, profile, base_dir):
    """Test 3: Validate all components initialize."""
    print("\n=== Test 3: Initialization Validation ===\n")

    try:
        from src.core.storage import init_db
        from src.core.scheduler import create_scheduler

        # Resolve DB path
        db_path = settings.get("storage", {}).get("db_path", "data/jobsentinel.db")
        if not os.path.isabs(db_path):
            db_path = os.path.join(base_dir, db_path)

        print(f"✓ Initializing database at {db_path}...")
        init_db(db_path)

        print("✓ Creating scheduler...")
        scheduler = create_scheduler(base_dir, settings)
        assert scheduler is not None, "Scheduler is None"
        assert scheduler.interval_seconds == settings.get("app", {}).get("run_interval_seconds", 300)

        print("✓ Scheduler properties:")
        print(f"  - Base dir: {scheduler.base_dir}")
        print(f"  - Interval: {scheduler.interval_seconds}s")
        print(f"  - Running: {scheduler._running}")

        print("\n✅ All components initialized successfully")
        return True, scheduler, db_path

    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_discovery_component():
    """Test 4: Validate discovery component structure."""
    print("\n=== Test 4: Discovery Component Validation ===\n")

    try:
        with patch("src.platforms.linkedin.collector.collect_jobs", return_value=[]), \
             patch("src.platforms.indeed.collector.collect_jobs", return_value=[]), \
             patch("src.platforms.naukri.collector.collect_jobs", return_value=[]):

            from src.discovery import JobDiscovery, create_discovery
            from src.core.config import load_settings, load_profile

            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            settings = load_settings(base_dir)
            profile = load_profile(base_dir)

            print("✓ Creating discovery component...")
            discovery = create_discovery(settings, profile)
            assert discovery is not None, "Discovery is None"
            assert isinstance(discovery, JobDiscovery), "Not a JobDiscovery instance"

            print("✓ Discovery component methods:")
            assert hasattr(discovery, "collect_all"), "Missing collect_all method"
            assert hasattr(discovery, "collect_linkedin"), "Missing collect_linkedin method"
            assert hasattr(discovery, "collect_indeed"), "Missing collect_indeed method"
            assert hasattr(discovery, "collect_naukri"), "Missing collect_naukri method"
            print("  - collect_all() ✓")
            print("  - collect_linkedin() ✓")
            print("  - collect_indeed() ✓")
            print("  - collect_naukri() ✓")

            print("✓ Testing collect_all()...")
            jobs = discovery.collect_all(enabled_override=[])
            assert isinstance(jobs, list), "collect_all() should return a list"
            print(f"  - Returned: {type(jobs).__name__} with {len(jobs)} items")

            print("\n✅ Discovery component validated")
            return True

    except Exception as e:
        print(f"\n❌ Discovery component validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_transitions():
    """Test 5: Validate state transitions."""
    print("\n=== Test 5: State Transition Validation ===\n")

    try:
        from backend.runtime.task_model import Task, TaskStatus

        print("✓ Creating test task...")
        task = Task(
            task_id="test_001",
            job_id="job_001",
            source_platform="linkedin",
            status=TaskStatus.DISCOVERED
        )
        print(f"  - Initial status: {task.status}")
        assert task.status == TaskStatus.DISCOVERED, "Should start as DISCOVERED"

        print("✓ Testing state transitions...")

        # DISCOVERED → QUEUED
        task.mark_queued()
        assert task.status == TaskStatus.QUEUED, "Should be QUEUED"
        print(f"  - After mark_queued(): {task.status}")

        # QUEUED → RUNNING
        task.mark_running()
        assert task.status == TaskStatus.RUNNING, "Should be RUNNING"
        print(f"  - After mark_running(): {task.status}")

        # RUNNING → COMPLETED
        task.mark_completed()
        assert task.status == TaskStatus.COMPLETED, "Should be COMPLETED"
        print(f"  - After mark_completed(): {task.status}")

        print("\n✅ State transitions work correctly")
        return True

    except Exception as e:
        print(f"\n❌ State transitions failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manual_review():
    """Test 6: Validate manual review flow."""
    print("\n=== Test 6: Manual Review Flow Validation ===\n")

    try:
        from backend.manual_review.review_queue import ReviewQueue
        from backend.runtime.task_model import Task, TaskStatus

        print("✓ Creating review queue...")
        review_queue = ReviewQueue()

        print("✓ Creating task for review...")
        task = Task(
            task_id="review_test_001",
            job_id="job_review_001",
            source_platform="linkedin",
            status=TaskStatus.MANUAL_REVIEW
        )

        print("✓ Adding task to review queue...")
        review_queue.add_for_review(task, reason="test_review")

        print("✓ Checking review queue...")
        pending = review_queue.get_pending_reviews()
        print(f"  - Pending reviews: {len(pending)}")
        assert len(pending) > 0, "Should have pending reviews"

        print("\n✅ Manual review flow works correctly")
        return True

    except Exception as e:
        print(f"\n❌ Manual review flow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_bus():
    """Test 7: Validate event bus."""
    print("\n=== Test 7: Event Bus Validation ===\n")

    try:
        from backend.events.event_bus import EventBus

        print("✓ Creating event bus...")
        bus = EventBus()

        print("✓ Testing event subscription...")
        events_received = []

        def handler(event):
            events_received.append(event)

        bus.subscribe("test_event", handler)

        print("✓ Emitting test event...")
        bus.emit("test_event", {"data": "test"})

        print(f"  - Events received: {len(events_received)}")
        assert len(events_received) > 0, "Should have received event"

        print("\n✅ Event bus works correctly")
        return True

    except Exception as e:
        print(f"\n❌ Event bus validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_queue_system():
    """Test 8: Validate queue system."""
    print("\n=== Test 8: Queue System Validation ===\n")

    try:
        from backend.queue.queue import TaskQueue
        from backend.runtime.task_model import Task, TaskStatus

        print("✓ Creating task queue...")
        queue = TaskQueue()

        print("✓ Creating test task...")
        task = Task(
            task_id="queue_test_001",
            job_id="job_queue_001",
            source_platform="linkedin",
            status=TaskStatus.QUEUED
        )

        print("✓ Enqueueing task...")
        queue.enqueue(task)

        print("✓ Checking queue size...")
        size = queue.size()
        print(f"  - Queue size: {size}")
        assert size > 0, "Queue should have tasks"

        print("✓ Dequeueing task...")
        dequeued = queue.dequeue()
        assert dequeued is not None, "Should dequeue a task"
        assert dequeued.task_id == task.task_id, "Should be the same task"

        print("\n✅ Queue system works correctly")
        return True

    except Exception as e:
        print(f"\n❌ Queue system validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_controller_dependency():
    """Test 9: Verify scheduler doesn't depend on controller."""
    print("\n=== Test 9: Scheduler Independence Validation ===\n")

    try:
        import inspect
        from src.core.scheduler import RuntimeScheduler

        print("✓ Checking scheduler imports...")
        source = inspect.getsource(RuntimeScheduler)

        # Check that scheduler doesn't import controller
        assert "from src.core.controller import" not in source, "Scheduler should not import controller"
        assert "import controller" not in source, "Scheduler should not import controller"

        print("  - No controller imports found ✓")

        print("✓ Checking scheduler uses discovery...")
        assert "from src.discovery import" in source or "src.discovery" in source, "Scheduler should use discovery"
        print("  - Discovery imports found ✓")

        print("\n✅ Scheduler is independent of controller")
        return True

    except Exception as e:
        print(f"\n❌ Scheduler independence validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("PHASE 1.5 - RUNTIME VALIDATION TEST SUITE")
    print("="*70)

    results = {}

    # Test 1: Imports
    results["imports"] = test_imports_with_mocking()
    if not results["imports"]:
        print("\n⚠️  Import validation failed - continuing with other tests")

    # Test 2: Configuration
    results["config"], settings, profile, base_dir = test_configuration()
    if not results["config"]:
        print("\n⚠️  Configuration validation failed - cannot continue with dependent tests")
        return results

    # Test 3: Initialization
    results["init"], scheduler, db_path = test_initialization(settings, profile, base_dir)

    # Test 4: Discovery
    results["discovery"] = test_discovery_component()

    # Test 5: State Transitions
    results["state_transitions"] = test_state_transitions()

    # Test 6: Manual Review
    results["manual_review"] = test_manual_review()

    # Test 7: Event Bus
    results["event_bus"] = test_event_bus()

    # Test 8: Queue System
    results["queue"] = test_queue_system()

    # Test 9: Scheduler Independence
    results["scheduler_independence"] = test_no_controller_dependency()

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
        print("\n✅ ALL VALIDATION TESTS PASSED")
        print("Runtime backbone is stable and ready for use")
    else:
        print(f"\n⚠️  {total - passed} VALIDATION TEST(S) FAILED")
        print("See details above for issues to fix")

    return results


if __name__ == "__main__":
    results = main()
    sys.exit(0 if all(results.values()) else 1)

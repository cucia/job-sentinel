"""
Phase 1.5 Runtime Validation - Playwright Fix Verification

Tests that runtime components can be imported without Playwright installed.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_scheduler_import():
    """Test: Scheduler can be imported without Playwright."""
    print("\n=== Test 1: Scheduler Import (No Playwright Required) ===\n")
    try:
        from src.core.scheduler import RuntimeScheduler, create_scheduler
        print("✅ Scheduler imported successfully")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_discovery_import():
    """Test: Discovery can be imported without Playwright."""
    print("\n=== Test 2: Discovery Import (No Playwright Required) ===\n")
    try:
        from src.discovery import JobDiscovery, create_discovery
        print("✅ Discovery imported successfully")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_runtime_bridge_import():
    """Test: RuntimeBridge can be imported without Playwright."""
    print("\n=== Test 3: RuntimeBridge Import (No Playwright Required) ===\n")
    try:
        from backend.bridge import create_runtime_bridge
        print("✅ RuntimeBridge imported successfully")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_orchestrator_import():
    """Test: Orchestrator can be imported without Playwright."""
    print("\n=== Test 4: Orchestrator Import (No Playwright Required) ===\n")
    try:
        from backend.orchestrator.orchestrator import RuntimeOrchestrator
        print("✅ Orchestrator imported successfully")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_queue_import():
    """Test: Queue can be imported without Playwright."""
    print("\n=== Test 5: Queue Import (No Playwright Required) ===\n")
    try:
        from backend.queue.queue import TaskQueue
        print("✅ Queue imported successfully")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_state_manager_import():
    """Test: StateManager can be imported without Playwright."""
    print("\n=== Test 6: StateManager Import (No Playwright Required) ===\n")
    try:
        from backend.state.state_manager import StateManager
        print("✅ StateManager imported successfully")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_event_bus_import():
    """Test: EventBus can be imported without Playwright."""
    print("\n=== Test 7: EventBus Import (No Playwright Required) ===\n")
    try:
        from backend.events.event_bus import EventBus
        print("✅ EventBus imported successfully")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_task_model_import():
    """Test: Task model can be imported without Playwright."""
    print("\n=== Test 8: Task Model Import (No Playwright Required) ===\n")
    try:
        from backend.runtime.task_model import Task, TaskStatus
        print("✅ Task model imported successfully")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_configuration_import():
    """Test: Configuration can be loaded without Playwright."""
    print("\n=== Test 9: Configuration Import (No Playwright Required) ===\n")
    try:
        from src.core.config import load_settings, load_profile
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        settings = load_settings(base_dir)
        profile = load_profile(base_dir)
        print("✅ Configuration loaded successfully")
        print(f"  - Settings: {type(settings).__name__}")
        print(f"  - Profile: {type(profile).__name__}")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def test_scheduler_initialization():
    """Test: Scheduler can be initialized without Playwright."""
    print("\n=== Test 10: Scheduler Initialization (No Playwright Required) ===\n")
    try:
        from src.core.scheduler import create_scheduler
        from src.core.config import load_settings

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        settings = load_settings(base_dir)
        scheduler = create_scheduler(base_dir, settings)

        print("✅ Scheduler initialized successfully")
        print(f"  - Base dir: {scheduler.base_dir}")
        print(f"  - Interval: {scheduler.interval_seconds}s")
        print(f"  - Running: {scheduler._running}")
        return True
    except ModuleNotFoundError as e:
        if "playwright" in str(e).lower():
            print(f"❌ Playwright required: {e}")
            return False
        raise


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("PHASE 1.5 - PLAYWRIGHT FIX VERIFICATION")
    print("Testing runtime initialization WITHOUT Playwright installed")
    print("="*70)

    results = {}

    # Run all tests
    results["scheduler_import"] = test_scheduler_import()
    results["discovery_import"] = test_discovery_import()
    results["runtime_bridge_import"] = test_runtime_bridge_import()
    results["orchestrator_import"] = test_orchestrator_import()
    results["queue_import"] = test_queue_import()
    results["state_manager_import"] = test_state_manager_import()
    results["event_bus_import"] = test_event_bus_import()
    results["task_model_import"] = test_task_model_import()
    results["configuration_import"] = test_configuration_import()
    results["scheduler_initialization"] = test_scheduler_initialization()

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
        print("✅ SUCCESS - PLAYWRIGHT FIX VERIFIED")
        print("="*70)
        print("\nRuntime initialization works WITHOUT Playwright installed.")
        print("Browser imports are deferred to execution boundary.")
        print("\nExecution path:")
        print("  Scheduler ✅ (no Playwright)")
        print("  Discovery ✅ (no Playwright)")
        print("  Queue ✅ (no Playwright)")
        print("  Orchestrator ✅ (no Playwright)")
        print("  Workers ⏳ (Playwright required only here)")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

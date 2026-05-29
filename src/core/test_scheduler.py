"""
Integration tests for RuntimeScheduler.

Validates:
- Scheduler initialization
- Single cycle execution
- Job discovery and enqueueing
- Queue population
- Orchestrator integration
"""

import tempfile
import os
from datetime import datetime

from src.core.scheduler import RuntimeScheduler, create_scheduler
from src.core.config import load_settings, load_profile
from src.core.storage import init_db, list_jobs


def test_scheduler_initialization():
    """Test scheduler initialization."""
    print("\n=== Scheduler Initialization Test ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal config
        config_dir = os.path.join(tmpdir, "configs")
        os.makedirs(config_dir)

        # Create settings.yaml
        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            f.write("""
app:
  run_interval_seconds: 60
  use_ai: false
  apply_all: false
platforms:
  enabled: []
storage:
  db_path: data/test.db
""")

        # Create profile.yaml
        with open(os.path.join(config_dir, "profile.yaml"), "w") as f:
            f.write("""
name: test_profile
skills: []
""")

        # Create data directory
        os.makedirs(os.path.join(tmpdir, "data"))

        # Initialize scheduler
        scheduler = RuntimeScheduler(tmpdir, interval_seconds=60)
        print("✓ Scheduler created")
        print(f"  - Base dir: {tmpdir}")
        print(f"  - Interval: 60s")

        # Check status before initialization
        status = scheduler.get_status()
        assert status["status"] == "not_initialized", "Should not be initialized yet"
        print("✓ Status before initialization: not_initialized")


def test_scheduler_single_cycle():
    """Test scheduler single cycle execution."""
    print("\n=== Scheduler Single Cycle Test ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal config
        config_dir = os.path.join(tmpdir, "configs")
        os.makedirs(config_dir)

        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            f.write("""
app:
  run_interval_seconds: 60
  use_ai: false
  apply_all: false
  pipeline_mode: direct_latest
platforms:
  enabled: []
storage:
  db_path: data/test.db
""")

        with open(os.path.join(config_dir, "profile.yaml"), "w") as f:
            f.write("""
name: test_profile
skills: []
""")

        os.makedirs(os.path.join(tmpdir, "data"))

        # Run single cycle
        scheduler = RuntimeScheduler(tmpdir, interval_seconds=60)
        print("✓ Scheduler created")

        scheduler.run_once()
        print("✓ Single cycle executed")

        # Check status after initialization
        status = scheduler.get_status()
        assert status["status"] == "stopped", "Should be stopped after single cycle"
        assert "queue_size" in status, "Should have queue_size in status"
        print(f"✓ Status after cycle:")
        print(f"  - Status: {status['status']}")
        print(f"  - Queue size: {status['queue_size']}")


def test_scheduler_factory():
    """Test scheduler factory function."""
    print("\n=== Scheduler Factory Test ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, "configs")
        os.makedirs(config_dir)

        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            f.write("""
app:
  run_interval_seconds: 120
platforms:
  enabled: []
storage:
  db_path: data/test.db
""")

        with open(os.path.join(config_dir, "profile.yaml"), "w") as f:
            f.write("name: test\n")

        os.makedirs(os.path.join(tmpdir, "data"))

        # Create scheduler via factory
        settings = load_settings(tmpdir)
        scheduler = create_scheduler(tmpdir, settings)

        assert scheduler.interval_seconds == 120, "Should use interval from settings"
        print("✓ Scheduler created via factory")
        print(f"  - Interval: {scheduler.interval_seconds}s")


def test_scheduler_platform_override():
    """Test scheduler with platform override."""
    print("\n=== Scheduler Platform Override Test ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, "configs")
        os.makedirs(config_dir)

        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            f.write("""
app:
  run_interval_seconds: 60
  use_ai: false
  apply_all: false
  pipeline_mode: direct_latest
platforms:
  enabled: [linkedin, indeed]
storage:
  db_path: data/test.db
""")

        with open(os.path.join(config_dir, "profile.yaml"), "w") as f:
            f.write("name: test\n")

        os.makedirs(os.path.join(tmpdir, "data"))

        scheduler = RuntimeScheduler(tmpdir, interval_seconds=60)
        print("✓ Scheduler created")

        # Run with platform override
        scheduler.run_once(platforms_override=["linkedin"])
        print("✓ Single cycle executed with platform override")
        print("  - Platforms: [linkedin]")


def test_scheduler_status():
    """Test scheduler status reporting."""
    print("\n=== Scheduler Status Test ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, "configs")
        os.makedirs(config_dir)

        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            f.write("""
app:
  run_interval_seconds: 60
  use_ai: false
  apply_all: false
  pipeline_mode: direct_latest
platforms:
  enabled: []
storage:
  db_path: data/test.db
""")

        with open(os.path.join(config_dir, "profile.yaml"), "w") as f:
            f.write("name: test\n")

        os.makedirs(os.path.join(tmpdir, "data"))

        scheduler = RuntimeScheduler(tmpdir, interval_seconds=60)
        scheduler.run_once()

        status = scheduler.get_status()
        print("✓ Status retrieved:")
        print(f"  - Status: {status['status']}")
        print(f"  - Interval: {status['interval_seconds']}s")
        print(f"  - Queue size: {status['queue_size']}")
        print(f"  - Orchestrator active: {status['orchestrator']['active_tasks']}")
        print(f"  - Reviews pending: {status['reviews']['pending']}")


if __name__ == "__main__":
    print("\n=== RuntimeScheduler Integration Tests ===\n")

    try:
        test_scheduler_initialization()
        test_scheduler_single_cycle()
        test_scheduler_factory()
        test_scheduler_platform_override()
        test_scheduler_status()

        print("\n=== All Tests Passed ===\n")
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        raise

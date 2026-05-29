"""
Minimal runtime scheduler for periodic job discovery and task enqueueing.

Responsibilities:
- Run at configurable intervals
- Trigger job discovery
- Convert discovered jobs into runtime tasks
- Enqueue tasks into the runtime queue
- Hand control to the orchestrator

Does NOT handle:
- Learning or feedback
- Memory systems
- Skills or agents
- ATS classification
- Worker execution (delegated to orchestrator)
"""

import argparse
import os
import time
from datetime import datetime


class RuntimeScheduler:
    """Minimal scheduler for periodic runtime execution."""

    def __init__(self, base_dir: str, interval_seconds: int = 300):
        """
        Initialize scheduler.

        Args:
            base_dir: Base directory for configuration
            interval_seconds: Interval between cycles (default 300s)
        """
        self.base_dir = base_dir
        self.interval_seconds = interval_seconds
        self._running = False
        self._bridge = None

    def _initialize(self) -> None:
        """Initialize runtime infrastructure."""
        from src.core.config import load_profile, load_settings
        from src.core.logger import log
        from src.core.platform_registry import get_platforms
        from src.core.storage import init_db
        from backend.bridge import create_runtime_bridge

        settings = load_settings(self.base_dir)
        profile = load_profile(self.base_dir)
        platforms = get_platforms()

        # Initialize database
        db_path = self._resolve_db_path(settings)
        init_db(db_path)

        # Create runtime bridge
        self._bridge = create_runtime_bridge(self.base_dir, settings, profile, platforms)
        log("[Scheduler] Runtime infrastructure initialized")

    def _resolve_db_path(self, settings: dict) -> str:
        """Resolve database path from settings."""
        db_path = settings.get("storage", {}).get("db_path", "data/jobsentinel.db")
        if os.path.isabs(db_path):
            return db_path
        return os.path.join(self.base_dir, db_path)

    def _run_cycle(self, platforms_override: list[str] = None) -> None:
        """
        Execute single discovery and enqueueing cycle.

        Args:
            platforms_override: Optional list of platforms to run
        """
        from src.core.config import load_settings, load_profile
        from src.core.logger import log
        from src.discovery import create_discovery

        settings = load_settings(self.base_dir)
        profile = load_profile(self.base_dir)

        # Discover jobs using dedicated discovery component
        discovery = create_discovery(settings, profile)
        jobs = discovery.collect_all(enabled_override=platforms_override)
        log(f"[Scheduler] Discovered {len(jobs)} jobs")

        if not jobs:
            return

        # Enqueue jobs into runtime
        task_ids = self._bridge.enqueue_jobs(jobs, priority=0)
        log(f"[Scheduler] Enqueued {len(task_ids)} tasks")

        # Log queue status
        queue_size = self._bridge.get_queue_size()
        log(f"[Scheduler] Queue size: {queue_size}")

    def run_once(self, platforms_override: list[str] = None) -> None:
        """
        Execute single cycle (for testing or manual execution).

        Args:
            platforms_override: Optional list of platforms to run
        """
        from src.core.logger import log

        try:
            if not self._bridge:
                self._initialize()
            self._run_cycle(platforms_override)
        except Exception as e:
            log(f"[Scheduler] Cycle error: {e}")

    def start(self, platforms_override: list[str] = None) -> None:
        """
        Start scheduler event loop.

        Args:
            platforms_override: Optional list of platforms to run
        """
        from src.core.logger import log

        log("[Scheduler] Starting")
        self._running = True
        self._initialize()

        try:
            while self._running:
                try:
                    self._run_cycle(platforms_override)
                except Exception as e:
                    log(f"[Scheduler] Cycle error: {e}")

                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            log("[Scheduler] Interrupted")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop scheduler gracefully."""
        from src.core.logger import log

        self._running = False
        log("[Scheduler] Stopped")

    def get_status(self) -> dict:
        """
        Get scheduler status.

        Returns:
            Status dict with queue and orchestrator info
        """
        if not self._bridge:
            return {"status": "not_initialized"}

        return {
            "status": "running" if self._running else "stopped",
            "interval_seconds": self.interval_seconds,
            "queue_size": self._bridge.get_queue_size(),
            "orchestrator": self._bridge.get_orchestrator_status(),
            "reviews": self._bridge.get_review_stats(),
        }


def create_scheduler(base_dir: str, settings: dict) -> RuntimeScheduler:
    """
    Factory function to create scheduler.

    Args:
        base_dir: Base directory
        settings: Application settings

    Returns:
        RuntimeScheduler instance
    """
    interval = int(settings.get("app", {}).get("run_interval_seconds", 300))
    return RuntimeScheduler(base_dir, interval_seconds=interval)


def main() -> None:
    """Main entry point for scheduler."""
    from src.core.config import load_settings
    from src.core.logger import log

    log("[Scheduler] JobSentinel started")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    settings = load_settings(base_dir)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="JobSentinel runtime scheduler")
    parser.add_argument(
        "--platforms",
        help="Comma-separated list of platforms to run (e.g., linkedin,naukri).",
        default="",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run single cycle and exit (for testing).",
    )
    args, _unknown = parser.parse_known_args()

    # Parse platform overrides
    platforms_arg = args.platforms.strip()
    env_platforms = os.environ.get("JOBSENTINEL_PLATFORMS", "").strip()
    platforms_override = []
    source = ""

    if platforms_arg:
        platforms_override = [p.strip() for p in platforms_arg.split(",") if p.strip()]
        source = "args"
    elif env_platforms:
        platforms_override = [p.strip() for p in env_platforms.split(",") if p.strip()]
        source = "env"

    if platforms_override:
        log(f"[Scheduler] Platform override ({source}): {platforms_override}")

    # Create and run scheduler
    scheduler = create_scheduler(base_dir, settings)

    if args.once:
        log("[Scheduler] Running single cycle")
        scheduler.run_once(platforms_override or None)
    else:
        scheduler.start(platforms_override or None)


if __name__ == "__main__":
    main()

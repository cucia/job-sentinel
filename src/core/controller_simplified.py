"""
Simplified controller.py - Discovery Only

Phase 1 Finalization: Controller reduced to single responsibility (job discovery)

Responsibilities:
- Collect jobs from all platforms
- Provide discovery interface for scheduler

Removed responsibilities (moved to runtime):
- Scheduling loop (→ scheduler.py)
- Job filtering (→ execution_pipeline.py)
- Job ranking (→ orchestrator)
- Job application (→ workers)
- Pipeline orchestration (→ orchestrator)
"""

import os
from src.core.config import load_profile, load_settings
from src.core.logger import log
from src.platforms.linkedin.collector import collect_jobs as collect_linkedin
from src.platforms.indeed.collector import collect_jobs as collect_indeed
from src.platforms.naukri.collector import collect_jobs as collect_naukri


def collect_jobs(settings: dict, profile: dict, enabled_override: list[str] | None = None) -> list:
    """
    Collect jobs from all enabled platforms.

    Args:
        settings: Application settings
        profile: User profile
        enabled_override: Optional list of platforms to run

    Returns:
        List of discovered jobs
    """
    enabled = enabled_override or settings.get("platforms", {}).get("enabled", [])
    jobs = []

    if "linkedin" in enabled:
        try:
            linkedin_jobs = collect_linkedin(settings, profile)
            log(f"[Discovery] LinkedIn: {len(linkedin_jobs)} jobs")
            jobs.extend(linkedin_jobs)
        except Exception as exc:
            log(f"[Discovery] LinkedIn failed: {exc}")

    if "indeed" in enabled:
        try:
            indeed_jobs = collect_indeed(settings, profile)
            log(f"[Discovery] Indeed: {len(indeed_jobs)} jobs")
            jobs.extend(indeed_jobs)
        except Exception as exc:
            log(f"[Discovery] Indeed failed: {exc}")

    if "naukri" in enabled:
        try:
            naukri_jobs = collect_naukri(settings, profile)
            log(f"[Discovery] Naukri: {len(naukri_jobs)} jobs")
            jobs.extend(naukri_jobs)
        except Exception as exc:
            log(f"[Discovery] Naukri failed: {exc}")

    log(f"[Discovery] Total: {len(jobs)} jobs")
    return jobs

"""
Discovery Component - Job Collection and Aggregation

Extracted from controller.py to provide a dedicated discovery interface.

Responsibilities:
- Collect jobs from all platforms (LinkedIn, Indeed, Naukri)
- Aggregate results
- Log collection metrics
- Provide unified discovery interface

This component is called directly by the scheduler, eliminating
the need for controller.py in the discovery phase.
"""

from src.core.logger import log


class JobDiscovery:
    """Unified job discovery interface for all platforms."""

    def __init__(self, settings: dict, profile: dict):
        """
        Initialize discovery component.

        Args:
            settings: Application settings
            profile: User profile
        """
        self.settings = settings
        self.profile = profile

    def collect_all(self, enabled_override: list[str] | None = None) -> list:
        """
        Collect jobs from all enabled platforms.

        Args:
            enabled_override: Optional list of platforms to run

        Returns:
            List of discovered jobs
        """
        from src.platforms.linkedin.collector import collect_jobs as collect_linkedin
        from src.platforms.indeed.collector import collect_jobs as collect_indeed
        from src.platforms.naukri.collector import collect_jobs as collect_naukri

        enabled = enabled_override or self.settings.get("platforms", {}).get("enabled", [])
        jobs = []

        if "linkedin" in enabled:
            try:
                linkedin_jobs = collect_linkedin(self.settings, self.profile)
                log(f"[Discovery] LinkedIn: {len(linkedin_jobs)} jobs")
                jobs.extend(linkedin_jobs)
            except Exception as exc:
                log(f"[Discovery] LinkedIn failed: {exc}")

        if "indeed" in enabled:
            try:
                indeed_jobs = collect_indeed(self.settings, self.profile)
                log(f"[Discovery] Indeed: {len(indeed_jobs)} jobs")
                jobs.extend(indeed_jobs)
            except Exception as exc:
                log(f"[Discovery] Indeed failed: {exc}")

        if "naukri" in enabled:
            try:
                naukri_jobs = collect_naukri(self.settings, self.profile)
                log(f"[Discovery] Naukri: {len(naukri_jobs)} jobs")
                jobs.extend(naukri_jobs)
            except Exception as exc:
                log(f"[Discovery] Naukri failed: {exc}")

        log(f"[Discovery] Total: {len(jobs)} jobs collected")
        return jobs

    def collect_linkedin(self) -> list:
        """
        Collect jobs from LinkedIn only.

        Returns:
            List of LinkedIn jobs
        """
        from src.platforms.linkedin.collector import collect_jobs as collect_linkedin

        try:
            jobs = collect_linkedin(self.settings, self.profile)
            log(f"[Discovery] LinkedIn: {len(jobs)} jobs")
            return jobs
        except Exception as exc:
            log(f"[Discovery] LinkedIn failed: {exc}")
            return []

    def collect_indeed(self) -> list:
        """
        Collect jobs from Indeed only.

        Returns:
            List of Indeed jobs
        """
        from src.platforms.indeed.collector import collect_jobs as collect_indeed

        try:
            jobs = collect_indeed(self.settings, self.profile)
            log(f"[Discovery] Indeed: {len(jobs)} jobs")
            return jobs
        except Exception as exc:
            log(f"[Discovery] Indeed failed: {exc}")
            return []

    def collect_naukri(self) -> list:
        """
        Collect jobs from Naukri only.

        Returns:
            List of Naukri jobs
        """
        from src.platforms.naukri.collector import collect_jobs as collect_naukri

        try:
            jobs = collect_naukri(self.settings, self.profile)
            log(f"[Discovery] Naukri: {len(jobs)} jobs")
            return jobs
        except Exception as exc:
            log(f"[Discovery] Naukri failed: {exc}")
            return []


def create_discovery(settings: dict, profile: dict) -> JobDiscovery:
    """
    Factory function to create discovery component.

    Args:
        settings: Application settings
        profile: User profile

    Returns:
        JobDiscovery instance
    """
    return JobDiscovery(settings, profile)

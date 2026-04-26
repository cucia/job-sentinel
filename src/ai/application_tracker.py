"""
Application Tracking System

Logs all job applications with detailed tracking of status, failures, and agent paths.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


class ApplicationTracker:
    """Tracks job applications and their outcomes."""

    def __init__(self, log_path: str = "data/application_logs.json"):
        self.log_path = log_path
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Ensure log file and directory exist."""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f:
                json.dump({"applications": []}, f, indent=2)

    def log_application(
        self,
        job_id: str,
        job_key: str,
        company: str,
        title: str,
        platform: str,
        status: str,
        task_context: Optional[Dict] = None,
        failure_reason: Optional[str] = None,
        agent_path: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Log a job application attempt.

        Args:
            job_id: Job identifier
            job_key: Job key
            company: Company name
            title: Job title
            platform: Platform name (linkedin, indeed, etc.)
            status: Application status (applied, failed, skipped, review)
            task_context: Full task context dict
            failure_reason: Reason for failure if applicable
            agent_path: List of agents involved in the flow
            metadata: Additional metadata
        """
        try:
            # Load existing logs
            with open(self.log_path, 'r') as f:
                data = json.load(f)

            # Extract agent path from task context if not provided
            if not agent_path and task_context:
                agent_path = self._extract_agent_path(task_context)

            # Create log entry
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "job_id": job_id,
                "job_key": job_key,
                "company": company,
                "title": title,
                "platform": platform,
                "status": status,
                "failure_reason": failure_reason,
                "agent_path": agent_path or [],
                "metadata": metadata or {},
            }

            # Add task context summary if available
            if task_context:
                entry["task_summary"] = {
                    "retry_count": task_context.get("retry_count", 0),
                    "errors": task_context.get("errors", []),
                    "ats_type": task_context.get("metadata", {}).get("ats_type"),
                    "form_detected": task_context.get("form_detected", False),
                    "fields_filled": len(task_context.get("filled_fields", [])),
                    "fields_missing": len(task_context.get("missing_fields", [])),
                    "submission_successful": task_context.get("submission_successful", False),
                }

            # Append to logs
            data["applications"].append(entry)

            # Write back
            with open(self.log_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as exc:
            # Don't fail the application if logging fails
            print(f"[Tracker] Failed to log application: {exc}")

    def _extract_agent_path(self, task_context: Dict) -> List[str]:
        """Extract agent execution path from task context."""
        agent_path = []
        attempts = task_context.get("attempts", [])

        for attempt in attempts:
            agent_type = attempt.get("agent_type")
            if agent_type and agent_type not in agent_path:
                agent_path.append(agent_type)

        return agent_path

    def get_statistics(self) -> Dict:
        """
        Get application statistics.

        Returns:
            Statistics dict with counts and success rates
        """
        try:
            with open(self.log_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            total = len(applications)

            if total == 0:
                return {
                    "total": 0,
                    "applied": 0,
                    "failed": 0,
                    "skipped": 0,
                    "review": 0,
                    "success_rate": 0.0,
                }

            status_counts = {
                "applied": 0,
                "failed": 0,
                "skipped": 0,
                "review": 0,
            }

            for app in applications:
                status = app.get("status", "unknown")
                if status in status_counts:
                    status_counts[status] += 1

            success_rate = (status_counts["applied"] / total) * 100 if total > 0 else 0.0

            return {
                "total": total,
                **status_counts,
                "success_rate": round(success_rate, 2),
            }

        except Exception:
            return {
                "total": 0,
                "applied": 0,
                "failed": 0,
                "skipped": 0,
                "review": 0,
                "success_rate": 0.0,
            }

    def get_failure_analysis(self) -> Dict[str, int]:
        """
        Analyze failure reasons.

        Returns:
            Dict mapping failure reasons to counts
        """
        try:
            with open(self.log_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            failure_counts = {}

            for app in applications:
                if app.get("status") in ["failed", "skipped"]:
                    reason = app.get("failure_reason", "unknown")
                    failure_counts[reason] = failure_counts.get(reason, 0) + 1

            return failure_counts

        except Exception:
            return {}

    def get_recent_applications(self, limit: int = 10) -> List[Dict]:
        """
        Get recent applications.

        Args:
            limit: Maximum number of applications to return

        Returns:
            List of recent application entries
        """
        try:
            with open(self.log_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            return applications[-limit:]

        except Exception:
            return []

    def get_platform_statistics(self) -> Dict[str, Dict]:
        """
        Get statistics per platform.

        Returns:
            Dict mapping platform names to their statistics
        """
        try:
            with open(self.log_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            platform_stats = {}

            for app in applications:
                platform = app.get("platform", "unknown")
                if platform not in platform_stats:
                    platform_stats[platform] = {
                        "total": 0,
                        "applied": 0,
                        "failed": 0,
                        "skipped": 0,
                        "review": 0,
                    }

                platform_stats[platform]["total"] += 1
                status = app.get("status", "unknown")
                if status in platform_stats[platform]:
                    platform_stats[platform][status] += 1

            # Calculate success rates
            for platform, stats in platform_stats.items():
                total = stats["total"]
                stats["success_rate"] = round((stats["applied"] / total) * 100, 2) if total > 0 else 0.0

            return platform_stats

        except Exception:
            return {}


# Global tracker instance
_tracker = None


def get_tracker(log_path: str = "data/application_logs.json") -> ApplicationTracker:
    """Get or create global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ApplicationTracker(log_path)
    return _tracker


def log_application(
    job_id: str,
    job_key: str,
    company: str,
    title: str,
    platform: str,
    status: str,
    task_context: Optional[Dict] = None,
    failure_reason: Optional[str] = None,
    agent_path: Optional[List[str]] = None,
    metadata: Optional[Dict] = None
) -> None:
    """Convenience function to log application."""
    tracker = get_tracker()
    tracker.log_application(
        job_id, job_key, company, title, platform, status,
        task_context, failure_reason, agent_path, metadata
    )

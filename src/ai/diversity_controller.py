"""
Application Diversity Controller

Prevents over-application to same company/role to maintain quality and avoid spam.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class DiversityController:
    """Controls application diversity to prevent redundant applications."""

    def __init__(self, tracker_path: str = "data/application_logs.json"):
        self.tracker_path = tracker_path
        self.default_company_cooldown_days = 30
        self.default_role_cooldown_days = 14

    def recently_applied(self, company: str, role: str, cooldown_days: int = None) -> dict:
        """
        Check if recently applied to similar company/role.

        Args:
            company: Company name
            role: Job role/title
            cooldown_days: Optional cooldown period (default: 30 for company, 14 for role)

        Returns:
            {
                "conflict": bool,
                "reason": str,
                "last_application": dict or None,
                "days_since": int or None
            }
        """
        if not os.path.exists(self.tracker_path):
            return {"conflict": False, "reason": "no_history", "last_application": None, "days_since": None}

        try:
            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])

            # Check company conflict
            company_conflict = self._check_company_conflict(
                applications,
                company,
                cooldown_days or self.default_company_cooldown_days
            )
            if company_conflict["conflict"]:
                return company_conflict

            # Check role conflict
            role_conflict = self._check_role_conflict(
                applications,
                company,
                role,
                cooldown_days or self.default_role_cooldown_days
            )
            if role_conflict["conflict"]:
                return role_conflict

            return {"conflict": False, "reason": "no_conflict", "last_application": None, "days_since": None}

        except Exception as exc:
            return {"conflict": False, "reason": f"error: {exc}", "last_application": None, "days_since": None}

    def _check_company_conflict(self, applications: List[dict], company: str, cooldown_days: int) -> dict:
        """Check if recently applied to same company."""
        company_lower = company.lower().strip()
        cutoff_date = datetime.now() - timedelta(days=cooldown_days)

        # Find recent applications to same company
        recent_company_apps = []
        for app in applications:
            app_company = (app.get("company") or "").lower().strip()
            if self._companies_match(app_company, company_lower):
                try:
                    app_date = datetime.fromisoformat(app.get("timestamp", ""))
                    if app_date >= cutoff_date:
                        recent_company_apps.append((app, app_date))
                except Exception:
                    continue

        if recent_company_apps:
            # Sort by date (most recent first)
            recent_company_apps.sort(key=lambda x: x[1], reverse=True)
            last_app, last_date = recent_company_apps[0]
            days_since = (datetime.now() - last_date).days

            return {
                "conflict": True,
                "reason": f"Applied to {company} {days_since} days ago (cooldown: {cooldown_days} days)",
                "last_application": last_app,
                "days_since": days_since,
            }

        return {"conflict": False, "reason": "no_company_conflict", "last_application": None, "days_since": None}

    def _check_role_conflict(self, applications: List[dict], company: str, role: str, cooldown_days: int) -> dict:
        """Check if recently applied to similar role at same company."""
        company_lower = company.lower().strip()
        role_lower = role.lower().strip()
        cutoff_date = datetime.now() - timedelta(days=cooldown_days)

        # Find recent applications to similar role at same company
        recent_role_apps = []
        for app in applications:
            app_company = (app.get("company") or "").lower().strip()
            app_title = (app.get("title") or "").lower().strip()

            if self._companies_match(app_company, company_lower) and self._roles_similar(app_title, role_lower):
                try:
                    app_date = datetime.fromisoformat(app.get("timestamp", ""))
                    if app_date >= cutoff_date:
                        recent_role_apps.append((app, app_date))
                except Exception:
                    continue

        if recent_role_apps:
            # Sort by date (most recent first)
            recent_role_apps.sort(key=lambda x: x[1], reverse=True)
            last_app, last_date = recent_role_apps[0]
            days_since = (datetime.now() - last_date).days

            return {
                "conflict": True,
                "reason": f"Applied to similar role at {company} {days_since} days ago (cooldown: {cooldown_days} days)",
                "last_application": last_app,
                "days_since": days_since,
            }

        return {"conflict": False, "reason": "no_role_conflict", "last_application": None, "days_since": None}

    def _companies_match(self, company1: str, company2: str) -> bool:
        """Check if two company names match (fuzzy matching)."""
        if not company1 or not company2:
            return False

        # Exact match
        if company1 == company2:
            return True

        # Remove common suffixes
        suffixes = ["inc", "llc", "ltd", "corp", "corporation", "company", "co"]
        c1 = company1
        c2 = company2
        for suffix in suffixes:
            c1 = c1.replace(f" {suffix}", "").replace(f".{suffix}", "")
            c2 = c2.replace(f" {suffix}", "").replace(f".{suffix}", "")

        # Check if one contains the other (for subsidiaries)
        if c1 in c2 or c2 in c1:
            return True

        return False

    def _roles_similar(self, role1: str, role2: str) -> bool:
        """Check if two roles are similar."""
        if not role1 or not role2:
            return False

        # Exact match
        if role1 == role2:
            return True

        # Extract key role terms
        role_terms1 = set(role1.split())
        role_terms2 = set(role2.split())

        # Check overlap (at least 50% of terms match)
        if len(role_terms1) == 0 or len(role_terms2) == 0:
            return False

        overlap = len(role_terms1 & role_terms2)
        min_terms = min(len(role_terms1), len(role_terms2))

        return overlap / min_terms >= 0.5

    def get_application_frequency(self, company: str = None, days: int = 30) -> dict:
        """
        Get application frequency statistics.

        Args:
            company: Optional company filter
            days: Time window in days

        Returns:
            {
                "total_applications": int,
                "applications_per_day": float,
                "unique_companies": int,
                "unique_roles": int
            }
        """
        if not os.path.exists(self.tracker_path):
            return {
                "total_applications": 0,
                "applications_per_day": 0.0,
                "unique_companies": 0,
                "unique_roles": 0,
            }

        try:
            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            cutoff_date = datetime.now() - timedelta(days=days)

            # Filter recent applications
            recent_apps = []
            for app in applications:
                try:
                    app_date = datetime.fromisoformat(app.get("timestamp", ""))
                    if app_date >= cutoff_date:
                        if company:
                            app_company = (app.get("company") or "").lower().strip()
                            if self._companies_match(app_company, company.lower().strip()):
                                recent_apps.append(app)
                        else:
                            recent_apps.append(app)
                except Exception:
                    continue

            # Calculate statistics
            total = len(recent_apps)
            per_day = total / days if days > 0 else 0.0
            unique_companies = len(set(app.get("company", "").lower() for app in recent_apps))
            unique_roles = len(set(app.get("title", "").lower() for app in recent_apps))

            return {
                "total_applications": total,
                "applications_per_day": round(per_day, 2),
                "unique_companies": unique_companies,
                "unique_roles": unique_roles,
            }

        except Exception:
            return {
                "total_applications": 0,
                "applications_per_day": 0.0,
                "unique_companies": 0,
                "unique_roles": 0,
            }

    def should_skip_for_diversity(self, job: dict, settings: dict = None) -> dict:
        """
        Check if should skip job for diversity reasons.

        Args:
            job: Job details
            settings: Optional settings with cooldown configuration

        Returns:
            {
                "should_skip": bool,
                "reason": str,
                "conflict_details": dict
            }
        """
        settings = settings or {}
        company = job.get("company", "")
        title = job.get("title", "")

        # Get cooldown settings
        company_cooldown = settings.get("diversity", {}).get("company_cooldown_days", self.default_company_cooldown_days)
        role_cooldown = settings.get("diversity", {}).get("role_cooldown_days", self.default_role_cooldown_days)

        # Check company conflict
        company_check = self.recently_applied(company, title, company_cooldown)
        if company_check["conflict"]:
            return {
                "should_skip": True,
                "reason": company_check["reason"],
                "conflict_details": company_check,
            }

        return {
            "should_skip": False,
            "reason": "no_diversity_conflict",
            "conflict_details": {},
        }


def get_diversity_controller() -> DiversityController:
    """Get or create diversity controller instance."""
    return DiversityController()

"""
Feedback Learning Loop

Analyzes application tracking data to continuously improve decision-making.
"""

import json
import os
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class FeedbackLearner:
    """Learns from application outcomes to improve future decisions."""

    def __init__(self, tracker_path: str = "data/application_logs.json"):
        self.tracker_path = tracker_path
        self.learning_state_path = "data/learning_state.json"
        self.learning_state = self._load_learning_state()

    def _load_learning_state(self) -> dict:
        """Load or initialize learning state."""
        if os.path.exists(self.learning_state_path):
            try:
                with open(self.learning_state_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "learned_patterns": {},
            "platform_insights": {},
            "role_insights": {},
            "last_learning_run": None,
            "total_samples": 0,
        }

    def _save_learning_state(self):
        """Save learning state to disk."""
        os.makedirs(os.path.dirname(self.learning_state_path), exist_ok=True)
        self.learning_state["last_learning_run"] = datetime.now().isoformat()
        with open(self.learning_state_path, 'w') as f:
            json.dump(self.learning_state, f, indent=2)

    def analyze_and_learn(self) -> dict:
        """
        Analyze application data and extract learnings.

        Returns:
            Learning insights dict
        """
        if not os.path.exists(self.tracker_path):
            return {"status": "no_data", "insights": []}

        try:
            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            if len(applications) < 5:
                return {"status": "insufficient_data", "insights": []}

            # Analyze different dimensions
            platform_insights = self._analyze_platform_performance(applications)
            role_insights = self._analyze_role_performance(applications)
            failure_insights = self._analyze_failure_patterns(applications)
            timing_insights = self._analyze_timing_patterns(applications)

            # Update learning state
            self.learning_state["platform_insights"] = platform_insights
            self.learning_state["role_insights"] = role_insights
            self.learning_state["total_samples"] = len(applications)
            self._save_learning_state()

            # Generate actionable insights
            insights = self._generate_insights(platform_insights, role_insights, failure_insights, timing_insights)

            return {
                "status": "success",
                "insights": insights,
                "platform_insights": platform_insights,
                "role_insights": role_insights,
                "failure_insights": failure_insights,
            }

        except Exception as exc:
            return {"status": "error", "error": str(exc), "insights": []}

    def _analyze_platform_performance(self, applications: List[dict]) -> dict:
        """Analyze success rates per platform."""
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
            stats["success_rate"] = round(stats["applied"] / total, 3) if total > 0 else 0.0

        return platform_stats

    def _analyze_role_performance(self, applications: List[dict]) -> dict:
        """Analyze success rates per role type."""
        role_stats = {}

        for app in applications:
            title = app.get("title", "").lower()
            role_type = self._extract_role_type(title)

            if role_type not in role_stats:
                role_stats[role_type] = {
                    "total": 0,
                    "applied": 0,
                    "failed": 0,
                }

            role_stats[role_type]["total"] += 1
            if app.get("status") == "applied":
                role_stats[role_type]["applied"] += 1
            elif app.get("status") == "failed":
                role_stats[role_type]["failed"] += 1

        # Calculate success rates
        for role, stats in role_stats.items():
            total = stats["total"]
            stats["success_rate"] = round(stats["applied"] / total, 3) if total > 0 else 0.0

        return role_stats

    def _extract_role_type(self, title: str) -> str:
        """Extract role type from job title."""
        if "analyst" in title:
            return "analyst"
        elif "engineer" in title:
            return "engineer"
        elif "developer" in title:
            return "developer"
        elif "security" in title:
            return "security"
        elif "data" in title:
            return "data"
        else:
            return "other"

    def _analyze_failure_patterns(self, applications: List[dict]) -> dict:
        """Analyze common failure reasons."""
        failure_reasons = {}

        for app in applications:
            if app.get("status") in ["failed", "skipped"]:
                reason = app.get("failure_reason", "unknown")
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        # Sort by frequency
        sorted_failures = sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)

        return {
            "top_failures": sorted_failures[:5],
            "total_failures": sum(failure_reasons.values()),
        }

    def _analyze_timing_patterns(self, applications: List[dict]) -> dict:
        """Analyze timing patterns (e.g., success by time of day)."""
        # For now, just track application volume over time
        recent_apps = []
        cutoff = datetime.now() - timedelta(days=7)

        for app in applications:
            try:
                app_date = datetime.fromisoformat(app.get("timestamp", ""))
                if app_date >= cutoff:
                    recent_apps.append(app)
            except Exception:
                continue

        return {
            "applications_last_7_days": len(recent_apps),
            "daily_average": round(len(recent_apps) / 7, 1),
        }

    def _generate_insights(self, platform_insights: dict, role_insights: dict, failure_insights: dict, timing_insights: dict) -> List[str]:
        """Generate actionable insights from analysis."""
        insights = []

        # Platform insights
        best_platform = max(platform_insights.items(), key=lambda x: x[1].get("success_rate", 0), default=None)
        if best_platform and best_platform[1]["success_rate"] > 0.60:
            insights.append(f"Focus on {best_platform[0]} - {best_platform[1]['success_rate']:.1%} success rate")

        worst_platform = min(platform_insights.items(), key=lambda x: x[1].get("success_rate", 1), default=None)
        if worst_platform and worst_platform[1]["success_rate"] < 0.30 and worst_platform[1]["total"] >= 5:
            insights.append(f"Reduce applications on {worst_platform[0]} - only {worst_platform[1]['success_rate']:.1%} success rate")

        # Role insights
        best_role = max(role_insights.items(), key=lambda x: x[1].get("success_rate", 0), default=None)
        if best_role and best_role[1]["success_rate"] > 0.60 and best_role[1]["total"] >= 3:
            insights.append(f"Prioritize {best_role[0]} roles - {best_role[1]['success_rate']:.1%} success rate")

        # Failure insights
        top_failures = failure_insights.get("top_failures", [])
        if top_failures:
            top_reason, count = top_failures[0]
            if count >= 5:
                insights.append(f"Address common failure: {top_reason} ({count} occurrences)")

        # Timing insights
        daily_avg = timing_insights.get("daily_average", 0)
        if daily_avg > 5:
            insights.append(f"High application rate ({daily_avg:.1f}/day) - consider increasing selectivity")

        return insights

    def get_recommendations(self, job: dict, profile: dict) -> dict:
        """
        Get recommendations based on learned patterns.

        Args:
            job: Job details
            profile: Candidate profile

        Returns:
            Recommendations dict
        """
        platform = job.get("platform", "unknown")
        title = job.get("title", "").lower()
        role_type = self._extract_role_type(title)

        recommendations = []
        confidence_boost = 0.0

        # Check platform performance
        platform_data = self.learning_state.get("platform_insights", {}).get(platform, {})
        platform_success = platform_data.get("success_rate", 0.0)

        if platform_success > 0.60:
            recommendations.append(f"Platform {platform} has {platform_success:.1%} success rate")
            confidence_boost += 0.10
        elif platform_success < 0.30 and platform_data.get("total", 0) >= 5:
            recommendations.append(f"Platform {platform} has low {platform_success:.1%} success rate")
            confidence_boost -= 0.15

        # Check role performance
        role_data = self.learning_state.get("role_insights", {}).get(role_type, {})
        role_success = role_data.get("success_rate", 0.0)

        if role_success > 0.60 and role_data.get("total", 0) >= 3:
            recommendations.append(f"Role type '{role_type}' has {role_success:.1%} success rate")
            confidence_boost += 0.10

        return {
            "recommendations": recommendations,
            "confidence_boost": confidence_boost,
            "platform_success_rate": platform_success,
            "role_success_rate": role_success,
        }


def get_feedback_learner() -> FeedbackLearner:
    """Get or create feedback learner instance."""
    return FeedbackLearner()

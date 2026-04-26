"""
Visibility Probability Predictor

Predicts the probability of application being seen by recruiters based on
job recency, platform patterns, timing, and historical data.
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
import re


class VisibilityPredictor:
    """Predicts visibility probability for job applications."""

    def __init__(self, tracker_path: str = "data/application_logs.json"):
        self.tracker_path = tracker_path
        self.baseline_visibility = 0.40  # 40% baseline visibility rate

    def predict_visibility(self, job: dict, platform: str, timing: dict = None) -> dict:
        """
        Predict probability of application being seen by recruiters.

        Args:
            job: Job details
            platform: Platform name
            timing: Optional timing context (hour_of_day, day_of_week)

        Returns:
            {
                "visibility_probability": 0.0-1.0,
                "confidence": 0-100,
                "factors": [str],
                "recommendation": "apply" | "wait" | "skip"
            }
        """
        # Start with baseline
        probability = self.baseline_visibility

        # Factor 1: Job recency (40% weight)
        recency_impact = self._recency_impact(job)
        probability += recency_impact * 0.40

        # Factor 2: Platform visibility patterns (25% weight)
        platform_impact = self._platform_visibility_impact(platform)
        probability += platform_impact * 0.25

        # Factor 3: Application timing (20% weight)
        timing_impact = self._timing_impact(timing or {})
        probability += timing_impact * 0.20

        # Factor 4: Competition level (15% weight)
        competition_impact = self._competition_impact(job)
        probability += competition_impact * 0.15

        # Clamp to 0-1 range
        probability = max(0.0, min(1.0, probability))

        # Calculate confidence
        confidence = self._calculate_confidence(platform)

        # Generate factors
        factors = self._generate_factors(recency_impact, platform_impact, timing_impact, competition_impact)

        # Make recommendation
        recommendation = self._make_recommendation(probability, recency_impact)

        return {
            "visibility_probability": round(probability, 3),
            "confidence": confidence,
            "factors": factors,
            "recommendation": recommendation,
        }

    def _recency_impact(self, job: dict) -> float:
        """
        Calculate impact from job posting recency.

        Returns: -0.20 to +0.40 adjustment
        """
        posted_text = (job.get("posted_text") or "").lower()
        posted_at = job.get("posted_at")

        # Try to parse posted_at timestamp
        if posted_at:
            try:
                posted_date = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                hours_ago = (datetime.now(posted_date.tzinfo) - posted_date).total_seconds() / 3600

                if hours_ago < 2:
                    return 0.40  # Very fresh - highest visibility
                elif hours_ago < 6:
                    return 0.35  # Fresh - high visibility
                elif hours_ago < 24:
                    return 0.25  # Recent - good visibility
                elif hours_ago < 72:
                    return 0.10  # 1-3 days - moderate visibility
                elif hours_ago < 168:
                    return 0.0   # 3-7 days - average
                else:
                    return -0.15  # Old - low visibility
            except Exception:
                pass

        # Fallback to text parsing
        if any(term in posted_text for term in ["just now", "few minutes", "1 minute", "2 minutes"]):
            return 0.40  # Very fresh
        elif any(term in posted_text for term in ["few hours", "1 hour", "2 hours", "3 hours"]):
            return 0.35  # Fresh
        elif any(term in posted_text for term in ["today", "4 hours", "5 hours", "6 hours"]):
            return 0.25  # Recent
        elif any(term in posted_text for term in ["yesterday", "1 day"]):
            return 0.10  # 1 day old
        elif any(term in posted_text for term in ["2 days", "3 days"]):
            return 0.0   # 2-3 days
        elif any(term in posted_text for term in ["4 days", "5 days", "6 days", "1 week"]):
            return -0.10  # Week old
        else:
            return -0.20  # Old posting

    def _platform_visibility_impact(self, platform: str) -> float:
        """
        Calculate impact from platform-specific visibility patterns.

        Returns: -0.10 to +0.25 adjustment
        """
        try:
            if not os.path.exists(self.tracker_path):
                return self._default_platform_visibility(platform)

            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            platform_apps = [app for app in applications if app.get("platform") == platform]

            if len(platform_apps) < 5:
                return self._default_platform_visibility(platform)

            # Calculate response rate (applied status indicates successful submission)
            applied = sum(1 for app in platform_apps if app.get("status") == "applied")
            response_rate = applied / len(platform_apps) if platform_apps else 0.0

            # Map response rate to visibility impact
            if response_rate >= 0.70:
                return 0.25  # High visibility platform
            elif response_rate >= 0.50:
                return 0.15  # Good visibility
            elif response_rate >= 0.30:
                return 0.05  # Average visibility
            else:
                return -0.10  # Low visibility

        except Exception:
            return self._default_platform_visibility(platform)

    def _default_platform_visibility(self, platform: str) -> float:
        """Default platform visibility patterns."""
        visibility_rates = {
            "linkedin": 0.15,      # LinkedIn Easy Apply has high volume, moderate visibility
            "greenhouse": 0.25,    # Direct ATS applications have better visibility
            "lever": 0.20,
            "workday": 0.15,
            "indeed": 0.05,        # Indeed has very high volume, lower visibility
            "naukri": 0.10,
        }
        return visibility_rates.get(platform, 0.0)

    def _timing_impact(self, timing: dict) -> float:
        """
        Calculate impact from application timing.

        Returns: -0.10 to +0.20 adjustment
        """
        now = datetime.now()
        hour = timing.get("hour_of_day", now.hour)
        day_of_week = timing.get("day_of_week", now.weekday())  # 0=Monday, 6=Sunday

        # Best times: weekday mornings (8-11am) when recruiters check applications
        if day_of_week < 5:  # Weekday
            if 8 <= hour <= 11:
                return 0.20  # Prime time - morning review
            elif 13 <= hour <= 16:
                return 0.10  # Afternoon - moderate
            elif 7 <= hour <= 18:
                return 0.05  # Business hours - average
            else:
                return -0.05  # After hours - lower visibility
        else:  # Weekend
            return -0.10  # Weekend applications get buried

    def _competition_impact(self, job: dict) -> float:
        """
        Calculate impact from competition level.

        Returns: -0.15 to +0.15 adjustment
        """
        description = (job.get("description") or "").lower()
        title = (job.get("title") or "").lower()

        # Check for high-competition signals
        high_competition_signals = [
            "100+ applicants",
            "200+ applicants",
            "500+ applicants",
            "many applicants",
            "highly competitive",
        ]

        low_competition_signals = [
            "urgently hiring",
            "immediate start",
            "hard to fill",
            "niche role",
            "specialized",
        ]

        text = f"{title} {description}"

        if any(signal in text for signal in high_competition_signals):
            return -0.15  # High competition reduces visibility
        elif any(signal in text for signal in low_competition_signals):
            return 0.15  # Low competition increases visibility
        else:
            return 0.0  # Average competition

    def _calculate_confidence(self, platform: str) -> int:
        """
        Calculate confidence in prediction.

        Returns: 0-100 confidence score
        """
        try:
            if not os.path.exists(self.tracker_path):
                return 50  # Moderate confidence without data

            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            platform_apps = [app for app in applications if app.get("platform") == platform]

            # More data = higher confidence
            data_points = len(platform_apps)
            if data_points >= 50:
                return 85
            elif data_points >= 20:
                return 70
            elif data_points >= 10:
                return 60
            else:
                return 50

        except Exception:
            return 50

    def _generate_factors(self, recency: float, platform: float, timing: float, competition: float) -> list:
        """Generate human-readable factors."""
        factors = []

        if recency > 0.30:
            factors.append("Very fresh posting - high visibility window")
        elif recency > 0.15:
            factors.append("Recent posting - good visibility")
        elif recency < -0.10:
            factors.append("Old posting - reduced visibility")

        if platform > 0.15:
            factors.append("Platform has strong visibility patterns")
        elif platform < -0.05:
            factors.append("Platform has low visibility rates")

        if timing > 0.10:
            factors.append("Optimal application timing (weekday morning)")
        elif timing < -0.05:
            factors.append("Suboptimal timing (after hours/weekend)")

        if competition > 0.10:
            factors.append("Low competition increases visibility")
        elif competition < -0.10:
            factors.append("High competition reduces visibility")

        return factors[:4]

    def _make_recommendation(self, probability: float, recency_impact: float) -> str:
        """Make application recommendation."""
        # If very fresh and good probability, apply immediately
        if recency_impact > 0.30 and probability >= 0.50:
            return "apply"
        # If good probability, apply
        elif probability >= 0.45:
            return "apply"
        # If moderate probability but very fresh, apply (time-sensitive)
        elif probability >= 0.35 and recency_impact > 0.25:
            return "apply"
        # If low probability but fresh, consider waiting for better timing
        elif probability >= 0.30 and recency_impact > 0.15:
            return "wait"
        # Otherwise skip
        else:
            return "skip"

    def get_platform_visibility_rates(self) -> Dict[str, float]:
        """
        Get visibility rates per platform from historical data.

        Returns:
            Dict mapping platform to visibility rate
        """
        try:
            if not os.path.exists(self.tracker_path):
                return {}

            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            platform_stats = {}

            for app in applications:
                platform = app.get("platform", "unknown")
                if platform not in platform_stats:
                    platform_stats[platform] = {"total": 0, "applied": 0}

                platform_stats[platform]["total"] += 1
                if app.get("status") == "applied":
                    platform_stats[platform]["applied"] += 1

            # Calculate rates
            rates = {}
            for platform, stats in platform_stats.items():
                total = stats["total"]
                applied = stats["applied"]
                rates[platform] = round(applied / total, 3) if total > 0 else 0.0

            return rates

        except Exception:
            return {}


def predict_visibility(job: dict, platform: str, timing: dict = None) -> dict:
    """
    Convenience function to predict visibility probability.

    Args:
        job: Job details
        platform: Platform name
        timing: Optional timing context

    Returns:
        Prediction dict with probability and recommendation
    """
    predictor = VisibilityPredictor()
    return predictor.predict_visibility(job, platform, timing)

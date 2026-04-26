"""
Shortlist Probability Predictor

Predicts the probability of getting shortlisted based on job fit,
historical success data, and platform patterns.
"""

import json
import os
from typing import Dict, Optional


class ShortlistPredictor:
    """Predicts shortlist probability for job applications."""

    def __init__(self, tracker_path: str = "data/application_logs.json"):
        self.tracker_path = tracker_path
        self.baseline_probability = 0.15  # 15% baseline shortlist rate

    def predict_shortlist(self, profile: dict, job: dict, quality_score: dict) -> dict:
        """
        Predict probability of getting shortlisted.

        Args:
            profile: Candidate profile
            job: Job details
            quality_score: Output from quality_scorer.evaluate_fit()

        Returns:
            {
                "probability": 0.0-1.0,
                "confidence": 0-100,
                "factors": [str],
                "recommendation": "apply" | "skip"
            }
        """
        # Start with baseline
        probability = self.baseline_probability

        # Factor 1: Quality score impact (40% weight)
        quality_impact = self._quality_score_impact(quality_score)
        probability += quality_impact * 0.40

        # Factor 2: Historical success rate (30% weight)
        historical_impact = self._historical_success_impact(job.get("platform"), profile)
        probability += historical_impact * 0.30

        # Factor 3: Platform patterns (20% weight)
        platform_impact = self._platform_pattern_impact(job.get("platform"))
        probability += platform_impact * 0.20

        # Factor 4: Job freshness (10% weight)
        freshness_impact = self._freshness_impact(job)
        probability += freshness_impact * 0.10

        # Clamp to 0-1 range
        probability = max(0.0, min(1.0, probability))

        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(job.get("platform"))

        # Generate factors
        factors = self._generate_factors(quality_score, historical_impact, platform_impact, freshness_impact)

        # Make recommendation
        recommendation = "apply" if probability >= 0.20 else "skip"

        return {
            "probability": round(probability, 3),
            "confidence": confidence,
            "factors": factors,
            "recommendation": recommendation,
        }

    def _quality_score_impact(self, quality_score: dict) -> float:
        """
        Calculate impact from quality score.

        Returns: -0.15 to +0.35 adjustment
        """
        overall = quality_score.get("overall_score", 50)
        tier = quality_score.get("quality_tier", "medium")

        if tier == "high":
            return 0.35
        elif tier == "medium":
            return 0.10
        else:
            return -0.15

    def _historical_success_impact(self, platform: str, profile: dict) -> float:
        """
        Calculate impact from historical success data.

        Returns: -0.10 to +0.30 adjustment
        """
        try:
            if not os.path.exists(self.tracker_path):
                return 0.0

            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            if not applications:
                return 0.0

            # Filter by platform
            platform_apps = [app for app in applications if app.get("platform") == platform]

            if not platform_apps:
                return 0.0

            # Calculate success rate
            total = len(platform_apps)
            applied = sum(1 for app in platform_apps if app.get("status") == "applied")
            success_rate = applied / total if total > 0 else 0.0

            # Map success rate to impact
            if success_rate >= 0.70:
                return 0.30  # High success rate
            elif success_rate >= 0.50:
                return 0.15  # Good success rate
            elif success_rate >= 0.30:
                return 0.0   # Average
            else:
                return -0.10  # Low success rate

        except Exception:
            return 0.0

    def _platform_pattern_impact(self, platform: str) -> float:
        """
        Calculate impact from platform-specific patterns.

        Returns: -0.05 to +0.20 adjustment
        """
        # Platform-specific shortlist rates (based on general patterns)
        platform_rates = {
            "linkedin": 0.18,   # LinkedIn Easy Apply has decent response
            "indeed": 0.12,     # Indeed has lower response rates
            "naukri": 0.15,     # Naukri moderate response
            "greenhouse": 0.22, # ATS platforms often have better tracking
            "lever": 0.20,
            "workday": 0.18,
        }

        baseline = 0.15
        platform_rate = platform_rates.get(platform, baseline)

        # Return adjustment from baseline
        return platform_rate - baseline

    def _freshness_impact(self, job: dict) -> float:
        """
        Calculate impact from job posting freshness.

        Returns: 0.0 to +0.10 adjustment
        """
        posted_text = (job.get("posted_text") or "").lower()

        if any(term in posted_text for term in ["just now", "today", "few hours"]):
            return 0.10  # Very fresh
        elif any(term in posted_text for term in ["1 day", "yesterday"]):
            return 0.05  # Fresh
        elif any(term in posted_text for term in ["2 day", "3 day"]):
            return 0.02  # Recent
        else:
            return 0.0   # Older posting

    def _calculate_confidence(self, platform: str) -> int:
        """
        Calculate confidence in prediction based on data availability.

        Returns: 0-100 confidence score
        """
        try:
            if not os.path.exists(self.tracker_path):
                return 40  # Low confidence without data

            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])
            platform_apps = [app for app in applications if app.get("platform") == platform]

            # More data = higher confidence
            data_points = len(platform_apps)
            if data_points >= 50:
                return 90
            elif data_points >= 20:
                return 75
            elif data_points >= 10:
                return 60
            else:
                return 45

        except Exception:
            return 40

    def _generate_factors(self, quality_score: dict, historical: float, platform: float, freshness: float) -> list:
        """Generate human-readable factors."""
        factors = []

        tier = quality_score.get("quality_tier", "medium")
        if tier == "high":
            factors.append("High quality job match")
        elif tier == "low":
            factors.append("Low quality match reduces probability")

        if historical > 0.15:
            factors.append("Strong historical success on this platform")
        elif historical < -0.05:
            factors.append("Low historical success on this platform")

        if platform > 0.05:
            factors.append("Platform has good response rates")

        if freshness > 0.05:
            factors.append("Fresh posting increases chances")

        return factors[:4]

    def get_platform_success_rates(self) -> Dict[str, float]:
        """
        Get success rates per platform from historical data.

        Returns:
            Dict mapping platform to success rate
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


def predict_shortlist(profile: dict, job: dict, quality_score: dict) -> dict:
    """
    Convenience function to predict shortlist probability.

    Args:
        profile: Candidate profile
        job: Job details
        quality_score: Output from quality_scorer.evaluate_fit()

    Returns:
        Prediction dict with probability and recommendation
    """
    predictor = ShortlistPredictor()
    return predictor.predict_shortlist(profile, job, quality_score)

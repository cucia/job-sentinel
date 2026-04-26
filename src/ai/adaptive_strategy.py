"""
Adaptive Strategy Engine

Adjusts application strategy based on success rates and feedback data.
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta


class AdaptiveStrategy:
    """Manages adaptive application strategy based on performance."""

    def __init__(self, tracker_path: str = "data/application_logs.json"):
        self.tracker_path = tracker_path
        self.strategy_state = self._load_strategy_state()

    def _load_strategy_state(self) -> dict:
        """Load or initialize strategy state."""
        state_path = "data/strategy_state.json"
        if os.path.exists(state_path):
            try:
                with open(state_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        # Default state
        return {
            "apply_rate_multiplier": 1.0,
            "min_quality_threshold": 60.0,
            "min_probability_threshold": 0.20,
            "prioritized_roles": [],
            "last_updated": datetime.now().isoformat(),
        }

    def _save_strategy_state(self):
        """Save strategy state to disk."""
        state_path = "data/strategy_state.json"
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        self.strategy_state["last_updated"] = datetime.now().isoformat()
        with open(state_path, 'w') as f:
            json.dump(self.strategy_state, f, indent=2)

    def get_strategy(self) -> dict:
        """
        Get current adaptive strategy.

        Returns:
            {
                "apply_rate_multiplier": float,
                "min_quality_threshold": float,
                "min_probability_threshold": float,
                "prioritized_roles": [str],
                "should_reduce_rate": bool,
                "should_increase_selectivity": bool
            }
        """
        # Analyze recent performance
        analysis = self._analyze_recent_performance()

        # Adjust strategy based on analysis
        self._adjust_strategy(analysis)

        return {
            "apply_rate_multiplier": self.strategy_state["apply_rate_multiplier"],
            "min_quality_threshold": self.strategy_state["min_quality_threshold"],
            "min_probability_threshold": self.strategy_state["min_probability_threshold"],
            "prioritized_roles": self.strategy_state["prioritized_roles"],
            "should_reduce_rate": self.strategy_state["apply_rate_multiplier"] < 1.0,
            "should_increase_selectivity": self.strategy_state["min_quality_threshold"] > 60.0,
        }

    def _analyze_recent_performance(self) -> dict:
        """
        Analyze recent application performance.

        Returns:
            Analysis dict with success rates and patterns
        """
        try:
            if not os.path.exists(self.tracker_path):
                return {"success_rate": 0.0, "total_applications": 0}

            with open(self.tracker_path, 'r') as f:
                data = json.load(f)

            applications = data.get("applications", [])

            # Filter to recent applications (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_apps = []
            for app in applications:
                try:
                    app_date = datetime.fromisoformat(app.get("timestamp", ""))
                    if app_date >= cutoff_date:
                        recent_apps.append(app)
                except Exception:
                    continue

            if not recent_apps:
                return {"success_rate": 0.0, "total_applications": 0}

            # Calculate success rate
            total = len(recent_apps)
            applied = sum(1 for app in recent_apps if app.get("status") == "applied")
            success_rate = applied / total if total > 0 else 0.0

            # Analyze by role
            role_stats = {}
            for app in recent_apps:
                title = app.get("title", "").lower()
                # Extract role type
                role_type = self._extract_role_type(title)
                if role_type not in role_stats:
                    role_stats[role_type] = {"total": 0, "applied": 0}
                role_stats[role_type]["total"] += 1
                if app.get("status") == "applied":
                    role_stats[role_type]["applied"] += 1

            # Find high-success roles
            high_success_roles = []
            for role, stats in role_stats.items():
                if stats["total"] >= 3:  # Minimum sample size
                    role_success_rate = stats["applied"] / stats["total"]
                    if role_success_rate >= 0.60:
                        high_success_roles.append(role)

            return {
                "success_rate": success_rate,
                "total_applications": total,
                "role_stats": role_stats,
                "high_success_roles": high_success_roles,
            }

        except Exception:
            return {"success_rate": 0.0, "total_applications": 0}

    def _extract_role_type(self, title: str) -> str:
        """Extract role type from job title."""
        title_lower = title.lower()
        if "analyst" in title_lower:
            return "analyst"
        elif "engineer" in title_lower:
            return "engineer"
        elif "developer" in title_lower:
            return "developer"
        elif "security" in title_lower:
            return "security"
        elif "data" in title_lower:
            return "data"
        else:
            return "other"

    def _adjust_strategy(self, analysis: dict):
        """
        Adjust strategy based on performance analysis.

        Args:
            analysis: Performance analysis dict
        """
        success_rate = analysis.get("success_rate", 0.0)
        total_apps = analysis.get("total_applications", 0)

        # Only adjust if we have enough data
        if total_apps < 10:
            return

        # Adjust apply rate based on success rate
        if success_rate < 0.30:
            # Low success rate - reduce apply rate and increase selectivity
            self.strategy_state["apply_rate_multiplier"] = 0.6
            self.strategy_state["min_quality_threshold"] = 70.0
            self.strategy_state["min_probability_threshold"] = 0.25
        elif success_rate < 0.50:
            # Below average - moderate reduction
            self.strategy_state["apply_rate_multiplier"] = 0.8
            self.strategy_state["min_quality_threshold"] = 65.0
            self.strategy_state["min_probability_threshold"] = 0.22
        elif success_rate >= 0.70:
            # High success rate - can be slightly less selective
            self.strategy_state["apply_rate_multiplier"] = 1.2
            self.strategy_state["min_quality_threshold"] = 55.0
            self.strategy_state["min_probability_threshold"] = 0.18
        else:
            # Good success rate - maintain current strategy
            self.strategy_state["apply_rate_multiplier"] = 1.0
            self.strategy_state["min_quality_threshold"] = 60.0
            self.strategy_state["min_probability_threshold"] = 0.20

        # Update prioritized roles
        high_success_roles = analysis.get("high_success_roles", [])
        if high_success_roles:
            self.strategy_state["prioritized_roles"] = high_success_roles

        # Save updated state
        self._save_strategy_state()

    def should_apply(self, quality_score: dict, shortlist_prediction: dict) -> dict:
        """
        Decide if should apply based on adaptive strategy.

        Args:
            quality_score: Output from quality_scorer
            shortlist_prediction: Output from shortlist_predictor

        Returns:
            {
                "should_apply": bool,
                "reason": str,
                "strategy_applied": str
            }
        """
        overall_score = quality_score.get("overall_score", 0)
        probability = shortlist_prediction.get("probability", 0)
        quality_tier = quality_score.get("quality_tier", "low")

        min_quality = self.strategy_state["min_quality_threshold"]
        min_probability = self.strategy_state["min_probability_threshold"]

        # Check quality threshold
        if overall_score < min_quality:
            return {
                "should_apply": False,
                "reason": f"Quality score {overall_score:.0f} below threshold {min_quality:.0f}",
                "strategy_applied": "quality_filter"
            }

        # Check probability threshold
        if probability < min_probability:
            return {
                "should_apply": False,
                "reason": f"Shortlist probability {probability:.2%} below threshold {min_probability:.2%}",
                "strategy_applied": "probability_filter"
            }

        # Always apply to high quality jobs
        if quality_tier == "high":
            return {
                "should_apply": True,
                "reason": "High quality match",
                "strategy_applied": "high_quality_priority"
            }

        # Apply adaptive rate multiplier for medium quality
        if quality_tier == "medium":
            multiplier = self.strategy_state["apply_rate_multiplier"]
            if multiplier < 1.0:
                # Being more selective - only apply if probability is good
                if probability >= min_probability * 1.2:
                    return {
                        "should_apply": True,
                        "reason": "Medium quality with good probability",
                        "strategy_applied": "selective_medium"
                    }
                else:
                    return {
                        "should_apply": False,
                        "reason": "Medium quality but probability not high enough in selective mode",
                        "strategy_applied": "selective_filter"
                    }
            else:
                return {
                    "should_apply": True,
                    "reason": "Medium quality meets thresholds",
                    "strategy_applied": "standard_medium"
                }

        # Low quality - skip
        return {
            "should_apply": False,
            "reason": "Low quality tier",
            "strategy_applied": "quality_tier_filter"
        }

    def get_performance_summary(self) -> dict:
        """Get performance summary for monitoring."""
        analysis = self._analyze_recent_performance()
        return {
            "success_rate": analysis.get("success_rate", 0.0),
            "total_applications": analysis.get("total_applications", 0),
            "current_strategy": self.strategy_state,
            "high_success_roles": analysis.get("high_success_roles", []),
        }


def get_adaptive_strategy() -> AdaptiveStrategy:
    """Get or create adaptive strategy instance."""
    return AdaptiveStrategy()

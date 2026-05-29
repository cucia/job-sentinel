"""
Execution pipeline extracted from controller.py

This module contains filtering, ranking, and orchestration logic
that was previously in controller.py. It's designed to be integrated
into the RuntimeOrchestrator for Phase 1 finalization.

Responsibilities:
- Job filtering (entry level, policy, AI, quality, visibility, diversity)
- Job ranking
- Job application
- Pipeline orchestration
"""

from src.core.logger import log
from src.core.policy import policy_allows
from src.core.storage import update_job, record_decision
from src.ai.scorer import evaluate_job
from src.ai.agents_wrapper import evaluate_job_with_agents
from src.ai.quality_scorer import evaluate_fit
from src.ai.shortlist_predictor import predict_shortlist
from src.ai.adaptive_strategy import get_adaptive_strategy
from src.ai.feedback_learner import get_feedback_learner
from src.ai.visibility_predictor import predict_visibility
from src.ai.diversity_controller import get_diversity_controller
from datetime import datetime


class ExecutionPipeline:
    """Execution pipeline for job filtering, ranking, and application."""

    def __init__(self, settings: dict, profile: dict, db_path: str, model_state: dict):
        """
        Initialize execution pipeline.

        Args:
            settings: Application settings
            profile: User profile
            db_path: Database path
            model_state: AI model state
        """
        self.settings = settings
        self.profile = profile
        self.db_path = db_path
        self.model_state = model_state

        # Load filtering components
        self.use_quality_filter = settings.get("ai", {}).get("use_quality_filter", False)
        self.use_visibility_filter = settings.get("ai", {}).get("use_visibility_filter", False)
        self.use_diversity_control = settings.get("ai", {}).get("use_diversity_control", False)
        self.use_ai = settings.get("app", {}).get("use_ai", False)
        self.use_policy = settings.get("app", {}).get("use_policy", False)
        self.entry_level_only = settings.get("app", {}).get("entry_level_only", True)

        self.seniority_blocklist = settings.get("app", {}).get(
            "seniority_blocklist",
            ["senior", "lead", "manager", "principal", "director", "head", "staff", "architect"],
        )

        # Initialize intelligent filtering components
        self.adaptive_strategy = None
        self.feedback_learner = None
        self.diversity_controller = None

        if self.use_quality_filter:
            self.adaptive_strategy = get_adaptive_strategy()
            self.feedback_learner = get_feedback_learner()
            log("[Pipeline] Quality filtering enabled")

        if self.use_diversity_control:
            self.diversity_controller = get_diversity_controller()
            log("[Pipeline] Diversity control enabled")

    def filter_job(self, job: dict) -> tuple[bool, str]:
        """
        Filter job through all configured filters.

        Args:
            job: Job to filter

        Returns:
            (should_apply, reason) tuple
        """
        # Entry level filter
        if self.entry_level_only:
            text = f"{job.get('title') or ''} {job.get('description') or ''}".lower()
            if any(term in text for term in self.seniority_blocklist):
                return False, "seniority_reject"

        # Policy filter
        if self.use_policy:
            policy = self.settings.get("policy", {})
            if not policy_allows(job, policy):
                return False, "policy_reject"

        # AI filter
        if self.use_ai:
            use_agents = self.settings.get("ai", {}).get("use_agents", False)
            if use_agents:
                decision = evaluate_job_with_agents(job, self.profile, self.settings)
            else:
                min_score = self.settings.get("ai", {}).get("min_score", 70)
                uncertainty_margin = self.settings.get("ai", {}).get("uncertainty_margin", 5)
                decision = evaluate_job(job, self.profile, min_score, uncertainty_margin, model_state=self.model_state)

            if not decision["apply"] and not decision["confused"]:
                return False, "ai_reject"

            if decision["confused"]:
                return False, "ai_review"

            # Diversity filter
            if self.use_diversity_control and self.diversity_controller:
                diversity_check = self.diversity_controller.should_skip_for_diversity(job, self.settings)
                if diversity_check["should_skip"]:
                    return False, "diversity_reject"

            # Visibility filter
            if self.use_visibility_filter:
                platform = job.get("platform", "unknown")
                timing = {"hour_of_day": datetime.now().hour, "day_of_week": datetime.now().weekday()}
                visibility_prediction = predict_visibility(job, platform, timing)
                if visibility_prediction["recommendation"] == "skip":
                    return False, "visibility_reject"

            # Quality filter
            if self.use_quality_filter:
                quality_score = evaluate_fit(self.profile, job)
                shortlist_prediction = predict_shortlist(self.profile, job, quality_score)
                strategy_decision = self.adaptive_strategy.should_apply(quality_score, shortlist_prediction)
                if not strategy_decision["should_apply"]:
                    return False, "quality_reject"

        return True, "accepted"

    def record_filter_decision(self, job: dict, reason: str, score: int = 0) -> None:
        """
        Record filtering decision to database.

        Args:
            job: Job that was filtered
            reason: Filter reason
            score: Optional score
        """
        update_job(self.db_path, job["job_key"], status="skipped")
        record_decision(self.db_path, job["job_key"], reason, score)

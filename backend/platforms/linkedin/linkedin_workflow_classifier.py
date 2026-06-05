"""
LinkedIn Workflow Classifier

Classifies LinkedIn job application workflows.
Integrates with existing ExecutionEngine architecture.
"""

import logging
from typing import Optional

from backend.platforms.linkedin.linkedin_page_data import (
    LinkedInPageData,
    LinkedInWorkflowType,
    LinkedInPageType,
)

logger = logging.getLogger(__name__)


class LinkedInWorkflowClassifier:
    """Classifies LinkedIn workflow types."""

    def __init__(self):
        """Initialize classifier."""
        pass

    def classify(self, page_data: LinkedInPageData) -> LinkedInWorkflowType:
        """
        Classify LinkedIn workflow type.

        Args:
            page_data: LinkedInPageData with page information

        Returns:
            LinkedInWorkflowType
        """
        logger.info(
            f"[Classifier] Classifying workflow: "
            f"page_type={page_data.page_type}, "
            f"easy_apply={page_data.easy_apply_available}, "
            f"external_apply={page_data.external_apply_available}"
        )

        # External redirect workflow
        if page_data.external_apply_available and not page_data.easy_apply_available:
            logger.info("[Classifier] Workflow: EXTERNAL_REDIRECT")
            return LinkedInWorkflowType.EXTERNAL_REDIRECT

        # Easy Apply workflow
        if page_data.easy_apply_available:
            # Determine if multi-step or single-step
            workflow_type = self._classify_easy_apply(page_data)
            logger.info(f"[Classifier] Workflow: {workflow_type}")
            return workflow_type

        # Unknown workflow
        logger.info("[Classifier] Workflow: UNKNOWN")
        return LinkedInWorkflowType.UNKNOWN

    def _classify_easy_apply(self, page_data: LinkedInPageData) -> LinkedInWorkflowType:
        """
        Classify Easy Apply workflow type (single vs multi-step).

        Args:
            page_data: LinkedInPageData

        Returns:
            EASY_APPLY or MULTI_STEP_EASY_APPLY
        """
        # Heuristics to detect multi-step:
        # - Job description contains "question" or "step" keywords
        # - Indicates additional questions in workflow
        # - Multi-step workflows typically have questions/additional steps

        if page_data.job_description:
            description_lower = page_data.job_description.lower()
            logger.info(f"[Classifier] Checking job description for multi-step indicators")
            if "question" in description_lower or "step" in description_lower:
                logger.info("[Classifier] Found multi-step indicators in job description")
                return LinkedInWorkflowType.MULTI_STEP_EASY_APPLY

        # Default to single-step Easy Apply
        logger.info("[Classifier] No multi-step indicators found, defaulting to single-step")
        return LinkedInWorkflowType.EASY_APPLY

    def get_workflow_characteristics(
        self, workflow_type: LinkedInWorkflowType
    ) -> dict:
        """
        Get characteristics for a workflow type.

        Args:
            workflow_type: LinkedInWorkflowType

        Returns:
            Dictionary with workflow characteristics
        """
        characteristics = {
            LinkedInWorkflowType.EASY_APPLY: {
                "name": "Easy Apply",
                "description": "Single-step LinkedIn Easy Apply workflow",
                "requires_external_navigation": False,
                "estimated_steps": 1,
                "uses_existing_profile": True,
            },
            LinkedInWorkflowType.MULTI_STEP_EASY_APPLY: {
                "name": "Multi-Step Easy Apply",
                "description": "Multi-step LinkedIn Easy Apply with questions",
                "requires_external_navigation": False,
                "estimated_steps": 3,
                "uses_existing_profile": True,
            },
            LinkedInWorkflowType.EXTERNAL_REDIRECT: {
                "name": "External Apply",
                "description": "Redirects to external company website",
                "requires_external_navigation": True,
                "estimated_steps": 5,
                "uses_existing_profile": False,
            },
            LinkedInWorkflowType.UNKNOWN: {
                "name": "Unknown",
                "description": "Unknown workflow type",
                "requires_external_navigation": None,
                "estimated_steps": None,
                "uses_existing_profile": None,
            },
        }

        return characteristics.get(
            workflow_type,
            {
                "name": "Unknown",
                "description": "Unknown workflow",
            },
        )

    def should_attempt_application(self, workflow_type: LinkedInWorkflowType) -> bool:
        """
        Determine if Job Sentinel should attempt application for this workflow.

        Args:
            workflow_type: LinkedInWorkflowType

        Returns:
            True if automation should be attempted
        """
        # Can automate LinkedIn workflows
        return workflow_type in (
            LinkedInWorkflowType.EASY_APPLY,
            LinkedInWorkflowType.MULTI_STEP_EASY_APPLY,
        )

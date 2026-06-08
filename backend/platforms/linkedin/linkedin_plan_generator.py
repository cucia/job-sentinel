"""
LinkedIn Plan Generator

Converts LinkedIn job pages into ExecutionPlans.
Reuses existing ExecutionPlan, ExecutionPlanStep, and ExecutionAction.

Does NOT execute plans - only generates them.
"""

import logging
from typing import Optional, List

from backend.application.session import ExecutionPlan, ExecutionPlanStep, ExecutionAction
from backend.platforms.linkedin import (
    LinkedInPageData,
    LinkedInWorkflowType,
)

logger = logging.getLogger(__name__)


class LinkedInPlanGenerator:
    """Generates ExecutionPlans for LinkedIn job applications."""

    def __init__(self):
        """Initialize plan generator."""
        pass

    def generate_plan(self, page_data: LinkedInPageData) -> Optional[ExecutionPlan]:
        """
        Generate ExecutionPlan for LinkedIn workflow.

        Args:
            page_data: LinkedInPageData with job and workflow information

        Returns:
            ExecutionPlan if applicable, None for external redirects
        """
        if not page_data:
            logger.warning("[PlanGenerator] No page data provided")
            return None

        logger.info(
            f"[PlanGenerator] Generating plan for {page_data.job_title} at {page_data.company_name}"
        )
        logger.info(f"[PlanGenerator] Workflow type: {page_data.workflow_type}")

        # Handle different workflow types
        if page_data.workflow_type == LinkedInWorkflowType.EASY_APPLY:
            return self._generate_easy_apply_plan(page_data)
        elif page_data.workflow_type == LinkedInWorkflowType.MULTI_STEP_EASY_APPLY:
            return self._generate_multi_step_plan(page_data)
        elif page_data.workflow_type == LinkedInWorkflowType.EXTERNAL_REDIRECT:
            logger.info("[PlanGenerator] External redirect - no plan generated")
            return None
        else:
            logger.warning(f"[PlanGenerator] Unknown workflow type: {page_data.workflow_type}")
            return None

    def _generate_easy_apply_plan(self, page_data: LinkedInPageData) -> ExecutionPlan:
        """
        Generate plan for single-step Easy Apply.

        Plan:
        1. Upload resume
        2. Submit application

        Note: Dynamic Question Engine will augment this plan with:
        - Form field filling steps
        - Question answering steps

        Args:
            page_data: LinkedInPageData

        Returns:
            ExecutionPlan with Easy Apply steps
        """
        logger.info("[PlanGenerator] Generating single-step Easy Apply plan")

        steps = []
        step_num = 1

        # Step 1: Upload resume
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.UPLOAD_RESUME,
                description="Upload resume for application",
                selector="input[type='file']",
                field_name="resume",
                value_source="profile.resume_path",
                expected_value=None,
                required=True,
                metadata={
                    "platform": "linkedin",
                    "job_title": page_data.job_title,
                    "company_name": page_data.company_name,
                }
            )
        )
        step_num += 1

        # Step 2: Submit application
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.SUBMIT_APPLICATION,
                description="Submit application",
                selector="button:has-text('Submit')",
                field_name="submit_button",
                required=True,
                metadata={
                    "platform": "linkedin",
                    "job_title": page_data.job_title,
                    "company_name": page_data.company_name,
                }
            )
        )
        step_num += 1

        plan = ExecutionPlan(
            plan_id=f"linkedin_easy_apply_{page_data.company_name or 'unknown'}",
            workflow_type="linkedin_easy_apply",
            job_id=page_data.job_title or "unknown",
            task_id="task_placeholder",
            steps=steps,
            total_estimated_duration=300,
            confidence_score=0.9,
        )

        logger.info(f"[PlanGenerator] Easy Apply plan generated: {len(steps)} steps")
        return plan

    def _generate_multi_step_plan(self, page_data: LinkedInPageData) -> ExecutionPlan:
        """
        Generate plan for multi-step Easy Apply.

        Plan:
        1. Upload resume
        2. Submit application

        Note: Dynamic Question Engine will augment this plan with:
        - Form field filling steps
        - Question answering steps

        Args:
            page_data: LinkedInPageData

        Returns:
            ExecutionPlan with multi-step steps
        """
        logger.info("[PlanGenerator] Generating multi-step Easy Apply plan")

        steps = []
        step_num = 1

        # Step 1: Upload resume
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.UPLOAD_RESUME,
                description="Upload resume for application",
                selector="input[type='file']",
                field_name="resume",
                value_source="profile.resume_path",
                expected_value=None,
                required=True,
                metadata={
                    "platform": "linkedin",
                    "job_title": page_data.job_title,
                    "company_name": page_data.company_name,
                }
            )
        )
        step_num += 1

        # Step 2: Submit application
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.SUBMIT_APPLICATION,
                description="Submit application",
                selector="button:has-text('Submit')",
                field_name="submit_button",
                required=True,
                metadata={
                    "platform": "linkedin",
                    "job_title": page_data.job_title,
                    "company_name": page_data.company_name,
                }
            )
        )
        step_num += 1

        plan = ExecutionPlan(
            plan_id=f"linkedin_multi_step_{page_data.company_name or 'unknown'}",
            workflow_type="linkedin_multi_step_easy_apply",
            job_id=page_data.job_title or "unknown",
            task_id="task_placeholder",
            steps=steps,
            total_estimated_duration=600,
            confidence_score=0.85,
        )

        logger.info(f"[PlanGenerator] Multi-step plan generated: {len(steps)} steps")
        return plan

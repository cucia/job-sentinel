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
        1. Fill profile information
        2. Upload resume
        3. Submit application

        Args:
            page_data: LinkedInPageData

        Returns:
            ExecutionPlan with Easy Apply steps
        """
        logger.info("[PlanGenerator] Generating single-step Easy Apply plan")

        steps = []
        step_num = 1

        # Step 1: Fill profile information
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.FILL_PROFILE,
                description="Fill LinkedIn profile information for application",
                selector=None,  # Will be detected during execution
                field_name="profile",
                value_source="linkedin_profile",
                required=True,
                metadata={
                    "platform": "linkedin",
                    "job_title": page_data.job_title,
                    "company_name": page_data.company_name,
                }
            )
        )
        step_num += 1

        # Step 2: Upload resume (if needed)
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.UPLOAD_RESUME,
                description="Upload resume for application",
                selector="input[type='file']",  # Common resume upload selector
                field_name="resume",
                value_source="user_profile",
                required=False,
            )
        )
        step_num += 1

        # Step 3: Submit application
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.SUBMIT_APPLICATION,
                description="Submit application",
                selector="button:has-text('Submit')",
                field_name="submit",
                value_source="static",
                required=True,
            )
        )

        # Create ExecutionPlan
        plan = ExecutionPlan(
            plan_id=f"linkedin_easy_apply_{self._sanitize_id(page_data.company_name)}",
            workflow_type="linkedin_easy_apply",
            job_id=f"linkedin_{self._sanitize_id(page_data.job_title)}",
            task_id=f"linkedin_apply_{self._sanitize_id(page_data.company_name)}",
            steps=steps,
            total_estimated_duration=300,  # 5 minutes estimated
            confidence_score=0.9,
        )

        # Store metadata in first step for reference
        if plan.steps:
            plan.steps[0].metadata = {
                "platform": "linkedin",
                "workflow_type": "linkedin_easy_apply",
                "job_title": page_data.job_title,
                "company_name": page_data.company_name,
                "location": page_data.location,
                "employment_type": page_data.employment_type,
                "experience_level": page_data.experience_level,
                "easy_apply": page_data.easy_apply_available,
            }

        logger.info(f"[PlanGenerator] Generated Easy Apply plan with {len(steps)} steps")
        return plan

    def _generate_multi_step_plan(self, page_data: LinkedInPageData) -> ExecutionPlan:
        """
        Generate plan for multi-step Easy Apply with questions.

        Plan:
        1. Fill profile information
        2. Continue
        3. Detect and answer questions
        4. Continue
        5. Upload resume
        6. Continue
        7. Submit application

        Args:
            page_data: LinkedInPageData

        Returns:
            ExecutionPlan with multi-step Easy Apply steps
        """
        logger.info("[PlanGenerator] Generating multi-step Easy Apply plan")

        steps = []
        step_num = 1

        # Step 1: Fill profile information
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.FILL_PROFILE,
                description="Fill LinkedIn profile information",
                selector=None,
                field_name="profile",
                value_source="linkedin_profile",
                required=True,
            )
        )
        step_num += 1

        # Step 2: Continue to next step
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.CONTINUE_TO_NEXT_STEP,
                description="Continue to next step",
                selector="button:has-text('Continue')",
                field_name="continue",
                value_source="static",
                required=True,
            )
        )
        step_num += 1

        # Step 3: Answer application questions
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.ANSWER_QUESTIONS,
                description="Answer application questions",
                selector=None,  # Will be detected during execution
                field_name="questions",
                value_source="detected",
                required=False,
            )
        )
        step_num += 1

        # Step 4: Continue to next step
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.CONTINUE_TO_NEXT_STEP,
                description="Continue to next step",
                selector="button:has-text('Continue')",
                field_name="continue",
                value_source="static",
                required=True,
            )
        )
        step_num += 1

        # Step 5: Upload resume
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.UPLOAD_RESUME,
                description="Upload resume",
                selector="input[type='file']",
                field_name="resume",
                value_source="user_profile",
                required=False,
            )
        )
        step_num += 1

        # Step 6: Continue to next step
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.CONTINUE_TO_NEXT_STEP,
                description="Continue to review and submit",
                selector="button:has-text('Continue')",
                field_name="continue",
                value_source="static",
                required=True,
            )
        )
        step_num += 1

        # Step 7: Submit application
        steps.append(
            ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.SUBMIT_APPLICATION,
                description="Submit application",
                selector="button:has-text('Submit')",
                field_name="submit",
                value_source="static",
                required=True,
            )
        )

        # Create ExecutionPlan
        plan = ExecutionPlan(
            plan_id=f"linkedin_multi_step_{self._sanitize_id(page_data.company_name)}",
            workflow_type="linkedin_multi_step_easy_apply",
            job_id=f"linkedin_{self._sanitize_id(page_data.job_title)}",
            task_id=f"linkedin_apply_{self._sanitize_id(page_data.company_name)}",
            steps=steps,
            total_estimated_duration=600,  # 10 minutes estimated
            confidence_score=0.85,
        )

        # Store metadata in first step for reference
        if plan.steps:
            plan.steps[0].metadata = {
                "platform": "linkedin",
                "workflow_type": "linkedin_multi_step_easy_apply",
                "job_title": page_data.job_title,
                "company_name": page_data.company_name,
                "location": page_data.location,
                "employment_type": page_data.employment_type,
                "experience_level": page_data.experience_level,
                "easy_apply": page_data.easy_apply_available,
                "multi_step": True,
            }

        logger.info(f"[PlanGenerator] Generated multi-step plan with {len(steps)} steps")
        return plan

    def _sanitize_id(self, text: str) -> str:
        """
        Sanitize text for use in IDs.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text (lowercase, no spaces/special chars)
        """
        if not text:
            return "unknown"
        # Convert to lowercase, replace spaces with underscores, remove special chars
        sanitized = text.lower().replace(" ", "_").replace(".", "")
        # Keep only alphanumeric and underscores
        sanitized = "".join(c if c.isalnum() or c == "_" else "" for c in sanitized)
        return sanitized[:50]  # Limit length

    def get_plan_summary(self, plan: ExecutionPlan) -> str:
        """
        Get human-readable summary of plan.

        Args:
            plan: ExecutionPlan

        Returns:
            Summary string
        """
        if not plan:
            return "No plan generated"

        # Get metadata from first step if available
        metadata = {}
        if plan.steps and plan.steps[0].metadata:
            metadata = plan.steps[0].metadata
        else:
            # Fallback: extract from plan fields
            metadata = {
                "platform": "linkedin",
                "job_title": "Unknown",
                "company_name": "Unknown",
                "workflow_type": plan.workflow_type,
            }

        lines = [
            f"Platform: {metadata.get('platform', 'unknown')}",
            f"Job: {metadata.get('job_title', 'Unknown')}",
            f"Company: {metadata.get('company_name', 'Unknown')}",
            f"Workflow: {metadata.get('workflow_type', 'Unknown')}",
            f"",
            f"Generated Plan ({len(plan.steps)} steps):",
        ]

        for step in plan.steps:
            lines.append(f"  {step.step_number}. {step.action.value}")

        lines.append(f"")
        lines.append(f"Estimated duration: {plan.total_estimated_duration}s")
        lines.append(f"Confidence score: {plan.confidence_score}")

        return "\n".join(lines)

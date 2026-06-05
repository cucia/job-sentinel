"""
Execution Planner

Generates workflow-specific execution plans based on page analysis results.

Plans describe what actions need to be taken, in what order, and what the
expected outcomes should be.

No execution - only planning.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional
from backend.application.session import (
    PageAnalysisResult,
    ExecutionPlan,
    ExecutionPlanStep,
    ExecutionAction,
)
from src.core.logger import log


class ExecutionPlanner:
    """Generates execution plans from page analysis."""

    def __init__(self, workflow_type: str):
        """
        Initialize planner for specific workflow.

        Args:
            workflow_type: Type of workflow (linkedin, linkedin_easy_apply, indeed, naukri)
        """
        # Map workflow_type variations to standard planner names
        workflow_mapping = {
            "linkedin": "linkedin",
            "linkedin_easy_apply": "linkedin",
            "indeed": "indeed",
            "naukri": "naukri",
            "generic": "generic",
        }

        self.workflow_type = workflow_mapping.get(workflow_type, "generic")
        self.plan_generators = {
            "linkedin": self._generate_linkedin_plan,
            "indeed": self._generate_indeed_plan,
            "naukri": self._generate_naukri_plan,
        }

    def generate_plan(
        self,
        job_id: str,
        task_id: str,
        page_analysis: PageAnalysisResult,
    ) -> ExecutionPlan:
        """
        Generate execution plan for current page.

        Args:
            job_id: Job identifier
            task_id: Task identifier
            page_analysis: Analysis of current page

        Returns:
            ExecutionPlan with steps and timeline
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        log(f"[ExecutionPlanner] Generating plan for {self.workflow_type}")
        log(f"  - Job: {job_id}")
        log(f"  - Page type: {page_analysis.page_type}")

        # Get workflow-specific generator
        generator = self.plan_generators.get(
            self.workflow_type,
            self._generate_generic_plan
        )

        # Generate steps
        steps = generator(page_analysis)

        # Calculate total duration
        total_duration = sum(step.estimated_duration_seconds for step in steps)

        # Calculate confidence
        confidence = self._calculate_confidence(page_analysis, steps)

        # Determine if manual review is needed
        requires_review = len(page_analysis.validation_messages) > 0

        plan = ExecutionPlan(
            plan_id=plan_id,
            workflow_type=self.workflow_type,
            job_id=job_id,
            task_id=task_id,
            steps=steps,
            total_estimated_duration=total_duration,
            confidence_score=confidence,
            requires_manual_review=requires_review,
            review_reasons=page_analysis.validation_messages,
        )

        log(f"  - Generated {len(steps)} step(s)")
        log(f"  - Estimated duration: {total_duration}s")
        log(f"  - Confidence: {confidence:.0%}")

        return plan

    def _generate_linkedin_plan(self, analysis: PageAnalysisResult) -> List[ExecutionPlanStep]:
        """Generate LinkedIn-specific execution plan."""
        steps = []
        step_num = 1

        # Determine page type and generate appropriate steps
        if "profile" in analysis.page_type:
            steps.extend(self._plan_profile_steps(step_num))
            step_num += len(steps)
        elif "questions" in analysis.page_type:
            steps.extend(self._plan_question_steps(step_num))
            step_num += len(steps)
        elif "review" in analysis.page_type:
            steps.extend(self._plan_review_steps(step_num))

        # Fallback to generic plan if no steps generated
        if len(steps) == 0:
            steps = self._generate_generic_plan(analysis)

        return steps

    def _generate_indeed_plan(self, analysis: PageAnalysisResult) -> List[ExecutionPlanStep]:
        """Generate Indeed-specific execution plan."""
        steps = []
        step_num = 1

        if "profile" in analysis.page_type:
            steps.extend(self._plan_indeed_profile_steps(step_num))
            step_num += len(steps)
        elif "questions" in analysis.page_type:
            steps.extend(self._plan_question_steps(step_num))
            step_num += len(steps)
        elif "review" in analysis.page_type:
            steps.extend(self._plan_review_steps(step_num))

        # Fallback to generic plan if no steps generated
        if len(steps) == 0:
            steps = self._generate_generic_plan(analysis)

        return steps

    def _generate_naukri_plan(self, analysis: PageAnalysisResult) -> List[ExecutionPlanStep]:
        """Generate Naukri-specific execution plan."""
        steps = []
        step_num = 1

        if "profile" in analysis.page_type:
            steps.extend(self._plan_naukri_profile_steps(step_num))
            step_num += len(steps)
        elif "questions" in analysis.page_type:
            steps.extend(self._plan_question_steps(step_num))
            step_num += len(steps)
        elif "review" in analysis.page_type:
            steps.extend(self._plan_review_steps(step_num))

        # Fallback to generic plan if no steps generated
        if len(steps) == 0:
            steps = self._generate_generic_plan(analysis)

        return steps

    def _generate_generic_plan(self, analysis: PageAnalysisResult) -> List[ExecutionPlanStep]:
        """Generate generic execution plan."""
        steps = []
        step_num = 1

        # Step 1: Upload resume if upload field exists
        if analysis.upload_fields:
            steps.append(ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.UPLOAD_RESUME,
                description="Upload resume document",
                required_fields=analysis.upload_fields,
                estimated_duration_seconds=30,
                validation_checks=["file_uploaded", "file_valid"],
                field_name="resume",
                value_source="profile.resume_path",
                required=True,
                metadata={
                    "upload_fields": analysis.upload_fields,
                    "field_type": "file",
                },
            ))
            step_num += 1

        # Step 2: Fill visible fields if they exist
        if analysis.visible_fields:
            steps.append(ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.FILL_PROFILE,
                description="Fill profile information",
                required_fields=analysis.visible_fields,
                estimated_duration_seconds=60,
                validation_checks=["required_fields_filled"],
                field_name="profile",
                value_source="user_profile",
                required=True,
                metadata={
                    "visible_fields": analysis.visible_fields,
                    "field_count": len(analysis.visible_fields),
                },
            ))
            step_num += 1

        # Step 3: Continue or submit
        if "submit" in analysis.next_action_hint or analysis.estimated_completion >= 0.9:
            steps.append(ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.SUBMIT_APPLICATION,
                description="Submit application",
                estimated_duration_seconds=10,
                validation_checks=["submission_successful"],
                selector="button[type='submit'], input[type='submit'], [data-action='submit']",
                field_name="submit_button",
                value_source="static",
                required=True,
                metadata={
                    "button_type": "submit",
                    "next_action": analysis.next_action_hint,
                },
            ))
        elif "continue" in str(analysis.navigation_actions):
            steps.append(ExecutionPlanStep(
                step_number=step_num,
                action=ExecutionAction.CONTINUE_TO_NEXT_STEP,
                description="Continue to next page",
                estimated_duration_seconds=5,
                validation_checks=["page_loaded"],
                selector="button[type='button'], a[data-action='continue'], .continue-button",
                field_name="continue_button",
                value_source="static",
                required=True,
                metadata={
                    "navigation_actions": str(analysis.navigation_actions),
                },
            ))

        return steps

    def _plan_profile_steps(self, start_step: int) -> List[ExecutionPlanStep]:
        """Plan profile filling steps."""
        return [
            ExecutionPlanStep(
                step_number=start_step,
                action=ExecutionAction.FILL_PROFILE,
                description="Fill LinkedIn profile information",
                estimated_duration_seconds=90,
                validation_checks=["all_fields_filled", "profile_complete"],
                field_name="profile",
                value_source="user_profile",
                required=True,
                metadata={
                    "platform": "linkedin",
                    "form_type": "profile",
                    "fields": ["firstName", "lastName", "headline", "location"],
                },
            ),
        ]

    def _plan_indeed_profile_steps(self, start_step: int) -> List[ExecutionPlanStep]:
        """Plan Indeed profile filling steps."""
        return [
            ExecutionPlanStep(
                step_number=start_step,
                action=ExecutionAction.UPLOAD_RESUME,
                description="Upload or select resume from Indeed database",
                estimated_duration_seconds=30,
                validation_checks=["resume_selected"],
                field_name="resume",
                value_source="profile.resume_path",
                required=True,
                metadata={
                    "platform": "indeed",
                    "form_type": "upload",
                    "allow_selection": True,
                },
            ),
            ExecutionPlanStep(
                step_number=start_step + 1,
                action=ExecutionAction.FILL_PROFILE,
                description="Fill profile information",
                estimated_duration_seconds=60,
                validation_checks=["required_fields_filled"],
                field_name="profile",
                value_source="user_profile",
                required=True,
                metadata={
                    "platform": "indeed",
                    "form_type": "profile",
                    "fields": ["email", "phone", "location"],
                },
            ),
        ]

    def _plan_naukri_profile_steps(self, start_step: int) -> List[ExecutionPlanStep]:
        """Plan Naukri profile filling steps."""
        return [
            ExecutionPlanStep(
                step_number=start_step,
                action=ExecutionAction.FILL_PROFILE,
                description="Fill Naukri profile information",
                estimated_duration_seconds=120,
                validation_checks=["profile_updated"],
                field_name="profile",
                value_source="user_profile",
                required=True,
                metadata={
                    "platform": "naukri",
                    "form_type": "profile",
                    "fields": ["email", "phone", "experience", "skills"],
                },
            ),
        ]

    def _plan_question_steps(self, start_step: int) -> List[ExecutionPlanStep]:
        """Plan question answering steps."""
        return [
            ExecutionPlanStep(
                step_number=start_step,
                action=ExecutionAction.ANSWER_QUESTIONS,
                description="Answer application questions",
                estimated_duration_seconds=120,
                validation_checks=["all_questions_answered", "answers_valid"],
                field_name="questions",
                value_source="ai_generated",
                required=True,
                metadata={
                    "form_type": "questions",
                    "requires_ai": True,
                },
            ),
        ]

    def _plan_review_steps(self, start_step: int) -> List[ExecutionPlanStep]:
        """Plan review and submission steps."""
        return [
            ExecutionPlanStep(
                step_number=start_step,
                action=ExecutionAction.CONFIRM_APPLICATION,
                description="Review application details",
                estimated_duration_seconds=30,
                validation_checks=["application_reviewed"],
                field_name="review",
                value_source="static",
                required=False,
                metadata={
                    "form_type": "review",
                    "user_action": "manual_review",
                },
            ),
            ExecutionPlanStep(
                step_number=start_step + 1,
                action=ExecutionAction.SUBMIT_APPLICATION,
                description="Submit application",
                estimated_duration_seconds=10,
                validation_checks=["submission_successful"],
                selector="button[type='submit'], input[type='submit'], [data-action='submit']",
                field_name="submit_button",
                value_source="static",
                required=True,
                metadata={
                    "form_type": "submit",
                    "button_type": "submit",
                },
            ),
            ExecutionPlanStep(
                step_number=start_step + 2,
                action=ExecutionAction.VERIFY_SUBMISSION,
                description="Verify application submitted successfully",
                estimated_duration_seconds=10,
                validation_checks=["confirmation_visible"],
                field_name="confirmation",
                value_source="static",
                required=False,
                metadata={
                    "form_type": "confirmation",
                    "selector_patterns": ["confirmation", "success", "submitted"],
                },
            ),
        ]

    def _calculate_confidence(
        self,
        analysis: PageAnalysisResult,
        steps: List[ExecutionPlanStep],
    ) -> float:
        """Calculate confidence score for execution plan."""
        confidence = 0.8  # Start with base confidence

        # Reduce confidence for unknown page types
        if analysis.page_type == "unknown":
            confidence -= 0.3

        # Reduce confidence if validation messages present
        if analysis.validation_messages:
            confidence -= 0.1

        # Increase confidence for well-known page types
        if any(known in analysis.page_type for known in ["profile", "questions", "review"]):
            confidence += 0.1

        # Clamp between 0 and 1
        return max(0.0, min(1.0, confidence))


def create_execution_planner(workflow_type: str) -> ExecutionPlanner:
    """Factory function to create execution planner."""
    return ExecutionPlanner(workflow_type)

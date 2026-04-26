"""
Multi-Agent System for Job Application Automation

This module implements specialized AI agents for different tasks:
- JobEvaluatorAgent: Evaluates if a job matches the candidate
- ApplicationAgent: Decides how to apply and fills forms
- ReviewAgent: Analyzes jobs that need human review
- StrategyAgent: Plans application strategy and prioritization
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.ai.llm import chat


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, profile: dict, settings: dict):
        self.profile = profile
        self.settings = settings
        self.llm_model = settings.get("ai", {}).get("llm_model", "llama3.2:latest")
        self.agent_name = self.__class__.__name__

    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Call the LLM with error handling."""
        try:
            # Check if using cloud provider
            use_cloud = self.settings.get("ai", {}).get("use_cloud", False)

            if use_cloud:
                from src.ai.cloud_llm import create_llm_client
                client = create_llm_client(self.settings)
                return client.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                )
            else:
                # Use local Ollama
                from src.ai.llm import chat
                return chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.llm_model,
                    temperature=temperature,
                )
        except Exception as exc:
            raise RuntimeError(f"{self.agent_name} LLM call failed: {exc}")


class JobEvaluatorAgent(BaseAgent):
    """Agent specialized in evaluating job matches."""

    def evaluate(self, job: dict) -> dict:
        """
        Evaluate if a job matches the candidate profile.

        Returns:
            {
                "decision": "APPLY" | "REJECT" | "REVIEW",
                "score": 0-100,
                "confidence": 0-100,
                "reasoning": str,
                "match_factors": [str],
                "concerns": [str]
            }
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_evaluation_prompt(job)

        response = self._call_llm(system_prompt, user_prompt)
        return self._parse_evaluation(response, job)

    def _build_system_prompt(self) -> str:
        skills = ", ".join(self.profile.get("skills", [])[:10])
        keywords = ", ".join(self.profile.get("keywords", [])[:10])
        role = self.profile.get("role", "cybersecurity professional")
        experience = self.profile.get("experience", "entry-level")

        return f"""You are a Job Evaluator Agent. Your sole purpose is to determine if a job matches a candidate's profile.

CANDIDATE PROFILE:
- Target Role: {role}
- Experience: {experience}
- Skills: {skills}
- Keywords: {keywords}

EVALUATION CRITERIA:
1. Skills Match: Does the job require skills the candidate has?
2. Experience Level: Is the seniority appropriate?
3. Role Alignment: Does this match their career goals?
4. Red Flags: Unrealistic requirements, mismatches, scams

DECISION RULES:
- APPLY: 70%+ match, candidate qualifies, good opportunity
- REJECT: <50% match, clear mismatch, or red flags
- REVIEW: 50-70% match, uncertain, or needs human judgment

Be analytical and precise. Focus on facts, not speculation."""

    def _build_evaluation_prompt(self, job: dict) -> str:
        return f"""Evaluate this job posting:

TITLE: {job.get('title', 'N/A')}
COMPANY: {job.get('company', 'N/A')}
LOCATION: {job.get('location', 'N/A')}
POSTED: {job.get('posted_text', job.get('posted_at', 'N/A'))}
EASY_APPLY: {'Yes' if job.get('easy_apply') else 'No'}

DESCRIPTION:
{job.get('description', 'No description available')[:3000]}

Respond in this EXACT format:
DECISION: <APPLY|REJECT|REVIEW>
SCORE: <0-100>
CONFIDENCE: <0-100>
REASONING: <2-3 sentences>
MATCH_FACTORS: <comma-separated list>
CONCERNS: <comma-separated list, or "none">"""

    def _parse_evaluation(self, response: str, job: dict) -> dict:
        decision = "REVIEW"
        score = 50
        confidence = 50
        reasoning = ""
        match_factors = []
        concerns = []

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip().upper()
            elif line.startswith("SCORE:"):
                try:
                    score = int(line.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = int(line.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
            elif line.startswith("MATCH_FACTORS:"):
                factors = line.split(":", 1)[1].strip()
                if factors.lower() != "none":
                    match_factors = [f.strip() for f in factors.split(",")]
            elif line.startswith("CONCERNS:"):
                concerns_text = line.split(":", 1)[1].strip()
                if concerns_text.lower() != "none":
                    concerns = [c.strip() for c in concerns_text.split(",")]

        apply = decision == "APPLY" and score >= 70 and confidence >= 60
        confused = decision == "REVIEW" or confidence < 60

        priority_score = score
        if job.get("easy_apply"):
            priority_score += 8

        return {
            "apply": apply,
            "confused": confused,
            "decision": decision,
            "score": score,
            "confidence": confidence,
            "priority_score": min(100, priority_score),
            "reasoning": reasoning,
            "match_factors": match_factors[:5],
            "concerns": concerns[:5],
            "agent": "JobEvaluatorAgent",
        }


class ApplicationAgent(BaseAgent):
    """Agent specialized in application strategy and form filling."""

    def plan_application(self, job: dict, evaluation: dict) -> dict:
        """
        Plan how to apply to a job.

        Returns:
            {
                "strategy": "easy_apply" | "manual" | "skip",
                "priority": "high" | "medium" | "low",
                "reasoning": str,
                "estimated_time": str
            }
        """
        system_prompt = f"""You are an Application Strategy Agent. You decide HOW to apply to jobs.

CANDIDATE PROFILE:
- Name: {self.profile.get('name', 'Candidate')}
- Email: {self.profile.get('email', 'N/A')}
- Phone: {self.profile.get('phone', 'N/A')}

YOUR TASK:
Given a job and its evaluation, determine the best application strategy.

STRATEGIES:
- easy_apply: Use platform's quick apply (LinkedIn Easy Apply, Indeed Quick Apply)
- manual: Apply through company website or complex forms
- skip: Don't apply (not worth the effort)

PRIORITY LEVELS:
- high: Strong match, apply immediately
- medium: Good match, apply when time permits
- low: Weak match, apply only if quota not met"""

        user_prompt = f"""Job: {job.get('title')} at {job.get('company')}
Evaluation Score: {evaluation.get('score')}/100
Easy Apply Available: {'Yes' if job.get('easy_apply') else 'No'}
Match Factors: {', '.join(evaluation.get('match_factors', []))}
Concerns: {', '.join(evaluation.get('concerns', []))}

Respond in this format:
STRATEGY: <easy_apply|manual|skip>
PRIORITY: <high|medium|low>
REASONING: <1-2 sentences>
ESTIMATED_TIME: <e.g., "2 minutes", "10 minutes">"""

        response = self._call_llm(system_prompt, user_prompt)
        return self._parse_strategy(response)

    def _parse_strategy(self, response: str) -> dict:
        strategy = "skip"
        priority = "low"
        reasoning = ""
        estimated_time = "unknown"

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("STRATEGY:"):
                strategy = line.split(":", 1)[1].strip().lower()
            elif line.startswith("PRIORITY:"):
                priority = line.split(":", 1)[1].strip().lower()
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
            elif line.startswith("ESTIMATED_TIME:"):
                estimated_time = line.split(":", 1)[1].strip()

        return {
            "strategy": strategy,
            "priority": priority,
            "reasoning": reasoning,
            "estimated_time": estimated_time,
            "agent": "ApplicationAgent",
        }


class ReviewAgent(BaseAgent):
    """Agent specialized in analyzing jobs that need human review."""

    def analyze_for_review(self, job: dict, evaluation: dict) -> dict:
        """
        Analyze why a job needs review and what the human should consider.

        Returns:
            {
                "review_reason": str,
                "questions": [str],
                "recommendation": str,
                "key_points": [str]
            }
        """
        system_prompt = """You are a Review Analysis Agent. You help humans make decisions on borderline jobs.

YOUR TASK:
Explain why a job needs human review and what factors the human should consider.

Be helpful and specific. Point out the key decision factors."""

        user_prompt = f"""Job: {job.get('title')} at {job.get('company')}
Evaluation Score: {evaluation.get('score')}/100
Confidence: {evaluation.get('confidence')}/100
Reasoning: {evaluation.get('reasoning')}
Match Factors: {', '.join(evaluation.get('match_factors', []))}
Concerns: {', '.join(evaluation.get('concerns', []))}

Description:
{job.get('description', '')[:2000]}

Respond in this format:
REVIEW_REASON: <why this needs human review>
QUESTIONS: <comma-separated questions the human should consider>
RECOMMENDATION: <your suggestion>
KEY_POINTS: <comma-separated key decision factors>"""

        response = self._call_llm(system_prompt, user_prompt, temperature=0.3)
        return self._parse_review(response)

    def _parse_review(self, response: str) -> dict:
        review_reason = ""
        questions = []
        recommendation = ""
        key_points = []

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("REVIEW_REASON:"):
                review_reason = line.split(":", 1)[1].strip()
            elif line.startswith("QUESTIONS:"):
                q_text = line.split(":", 1)[1].strip()
                questions = [q.strip() for q in q_text.split(",")]
            elif line.startswith("RECOMMENDATION:"):
                recommendation = line.split(":", 1)[1].strip()
            elif line.startswith("KEY_POINTS:"):
                kp_text = line.split(":", 1)[1].strip()
                key_points = [kp.strip() for kp in kp_text.split(",")]

        return {
            "review_reason": review_reason,
            "questions": questions[:5],
            "recommendation": recommendation,
            "key_points": key_points[:5],
            "agent": "ReviewAgent",
        }


class StrategyAgent(BaseAgent):
    """Agent specialized in overall application strategy and prioritization."""

    def prioritize_batch(self, jobs_with_evaluations: List[tuple]) -> List[dict]:
        """
        Prioritize a batch of jobs for application.

        Args:
            jobs_with_evaluations: List of (job, evaluation) tuples

        Returns:
            Sorted list of jobs with priority scores
        """
        if not jobs_with_evaluations:
            return []

        # Build summary for LLM
        job_summaries = []
        for idx, (job, eval_result) in enumerate(jobs_with_evaluations[:20]):  # Limit to 20 for LLM
            job_summaries.append(
                f"{idx+1}. {job.get('title')} at {job.get('company')} "
                f"(Score: {eval_result.get('score')}, Easy Apply: {job.get('easy_apply')})"
            )

        system_prompt = """You are a Strategy Agent. You prioritize which jobs to apply to first.

PRIORITIZATION FACTORS:
1. Match quality (higher score = higher priority)
2. Easy apply availability (faster applications)
3. Recency (newer postings = higher priority)
4. Company reputation
5. Growth potential

YOUR TASK:
Given a list of jobs, suggest the optimal application order."""

        user_prompt = f"""Prioritize these jobs for application:

{chr(10).join(job_summaries)}

Respond with:
TOP_PRIORITIES: <comma-separated job numbers (e.g., "3, 7, 1")>
REASONING: <why this order>"""

        try:
            response = self._call_llm(system_prompt, user_prompt, temperature=0.1)
            priority_order = self._parse_priorities(response, len(jobs_with_evaluations))
        except Exception:
            # Fallback: sort by score and easy_apply
            priority_order = list(range(len(jobs_with_evaluations)))

        # Reorder based on priorities
        prioritized = []
        for idx in priority_order:
            if idx < len(jobs_with_evaluations):
                job, evaluation = jobs_with_evaluations[idx]
                prioritized.append({
                    "job": job,
                    "evaluation": evaluation,
                    "priority_rank": len(prioritized) + 1,
                })

        return prioritized

    def _parse_priorities(self, response: str, total_jobs: int) -> List[int]:
        for line in response.split("\n"):
            if line.startswith("TOP_PRIORITIES:"):
                priorities_text = line.split(":", 1)[1].strip()
                try:
                    # Parse comma-separated numbers
                    priorities = [int(p.strip()) - 1 for p in priorities_text.split(",")]
                    # Add remaining jobs
                    remaining = [i for i in range(total_jobs) if i not in priorities]
                    return priorities + remaining
                except (ValueError, IndexError):
                    pass
        # Fallback: original order
        return list(range(total_jobs))


class NavigationAgent(BaseAgent):
    """Agent specialized in handling navigation and external redirects."""

    async def handle_navigation(self, task_context, page) -> dict:
        """
        Handle navigation to apply URL, detect redirects, and update context.

        Args:
            task_context: TaskContext object
            page: Playwright page object

        Returns:
            Navigation result with status and detected URLs
        """
        from src.ai.task_context import AgentType, TaskStatus

        task_context.add_attempt(
            AgentType.NAVIGATOR,
            "navigate_to_apply_url",
            "started"
        )

        try:
            apply_url = task_context.apply_url or task_context.source_url

            # Navigate to apply URL
            response = await page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
            task_context.current_url = page.url

            # Detect ATS type from URL and page content
            ats_type = await self._detect_ats_type(page)
            if ats_type:
                task_context.metadata["ats_type"] = ats_type
                task_context.add_attempt(
                    AgentType.NAVIGATOR,
                    "detect_ats",
                    "success",
                    metadata={"ats_type": ats_type}
                )

            # Check for external redirect
            if task_context.current_url != apply_url:
                task_context.external_redirect = True
                task_context.add_attempt(
                    AgentType.NAVIGATOR,
                    "detect_redirect",
                    "success",
                    metadata={"redirected_to": task_context.current_url}
                )

            # Detect if we're on a company career page
            is_company_page = await self._detect_company_page(page)
            if is_company_page:
                task_context.company_url = task_context.current_url

            # Check for authentication requirement
            auth_required = await self._detect_auth_required(page)
            if auth_required:
                task_context.auth_required = True
                task_context.add_error("Authentication required")
                return {
                    "success": False,
                    "reason": "auth_required",
                    "delegate_to": "recovery"
                }

            task_context.add_attempt(
                AgentType.NAVIGATOR,
                "navigate_to_apply_url",
                "success"
            )

            return {
                "success": True,
                "current_url": task_context.current_url,
                "external_redirect": task_context.external_redirect,
                "company_url": task_context.company_url,
                "delegate_to": "form_detector"
            }

        except Exception as exc:
            task_context.add_error(f"Navigation failed: {exc}")
            task_context.add_attempt(
                AgentType.NAVIGATOR,
                "navigate_to_apply_url",
                "failed",
                error=str(exc)
            )
            return {
                "success": False,
                "reason": "navigation_error",
                "error": str(exc),
                "delegate_to": "recovery"
            }

    async def _detect_company_page(self, page) -> bool:
        """Detect if current page is a company career page."""
        try:
            url = page.url.lower()
            career_indicators = ["career", "jobs", "apply", "opportunities", "join", "hiring"]
            return any(indicator in url for indicator in career_indicators)
        except Exception:
            return False

    async def _detect_auth_required(self, page) -> bool:
        """Detect if authentication/login is required."""
        try:
            # Check for common login indicators
            login_selectors = [
                "input[type='password']",
                "button:has-text('Sign in')",
                "button:has-text('Log in')",
                "a:has-text('Sign in')",
                ".login-form",
                "#login"
            ]
            for selector in login_selectors:
                element = await page.query_selector(selector)
                if element:
                    return True
            return False
        except Exception:
            return False

    async def _detect_ats_type(self, page) -> Optional[str]:
        """Detect ATS platform type from URL and page content."""
        try:
            from src.ai.field_maps import detect_ats_from_url, detect_ats_from_page

            # Check URL first
            ats_type = detect_ats_from_url(page.url)
            if ats_type:
                return ats_type

            # Check page content
            page_content = await page.content()
            ats_type = detect_ats_from_page(page_content)
            if ats_type:
                return ats_type

            return "generic"
        except Exception:
            return "generic"


class FormDetectionAgent(BaseAgent):
    """Agent specialized in detecting and analyzing forms."""

    async def detect_form(self, task_context, page) -> dict:
        """
        Scan DOM for forms and identify fields.

        Args:
            task_context: TaskContext object
            page: Playwright page object

        Returns:
            Detection result with form fields
        """
        from src.ai.task_context import AgentType, FormField

        task_context.add_attempt(
            AgentType.FORM_DETECTOR,
            "scan_for_forms",
            "started"
        )

        try:
            # Use ATS-specific field mapping if available
            ats_type = task_context.metadata.get("ats_type", "generic")
            use_ats_mapping = ats_type != "generic"

            if use_ats_mapping:
                task_context.add_attempt(
                    AgentType.FORM_DETECTOR,
                    "use_ats_mapping",
                    "started",
                    metadata={"ats_type": ats_type}
                )
                # Try ATS-specific detection first
                ats_fields_found = await self._detect_with_ats_map(page, task_context, ats_type)
                if ats_fields_found:
                    task_context.add_attempt(
                        AgentType.FORM_DETECTOR,
                        "use_ats_mapping",
                        "success",
                        metadata={"fields_found": ats_fields_found}
                    )

            # Find all form elements
            forms = await page.query_selector_all("form")

            if not forms:
                task_context.form_detected = False
                task_context.add_attempt(
                    AgentType.FORM_DETECTOR,
                    "scan_for_forms",
                    "no_forms_found"
                )
                return {
                    "success": False,
                    "reason": "no_forms_found",
                    "delegate_to": "recovery"
                }

            task_context.form_detected = True

            # Analyze form fields (generic detection as fallback)
            all_inputs = await page.query_selector_all("input, textarea, select")

            for input_el in all_inputs:
                try:
                    field_info = await self._extract_field_info(input_el)
                    if field_info:
                        task_context.detected_fields.append(field_info)
                except Exception:
                    continue

            # Identify required fields
            required_fields = [f for f in task_context.detected_fields if f.required]
            task_context.missing_fields = [f.name for f in required_fields]

            task_context.add_attempt(
                AgentType.FORM_DETECTOR,
                "scan_for_forms",
                "success",
                metadata={
                    "total_fields": len(task_context.detected_fields),
                    "required_fields": len(required_fields),
                    "ats_type": ats_type
                }
            )

            return {
                "success": True,
                "fields_detected": len(task_context.detected_fields),
                "required_fields": len(required_fields),
                "delegate_to": "form_filler"
            }

        except Exception as exc:
            task_context.add_error(f"Form detection failed: {exc}")
            task_context.add_attempt(
                AgentType.FORM_DETECTOR,
                "scan_for_forms",
                "failed",
                error=str(exc)
            )
            return {
                "success": False,
                "reason": "detection_error",
                "error": str(exc),
                "delegate_to": "recovery"
            }

    async def _extract_field_info(self, element) -> Optional['FormField']:
        """Extract information about a form field."""
        from src.ai.task_context import FormField

        try:
            field_type = await element.get_attribute("type") or "text"
            name = await element.get_attribute("name") or ""
            field_id = await element.get_attribute("id") or ""
            required = await element.get_attribute("required") is not None
            placeholder = await element.get_attribute("placeholder") or ""

            # Get label
            label = placeholder
            if field_id:
                label_el = await element.evaluate_handle(
                    f'(el) => document.querySelector("label[for=\\"{field_id}\\"]")'
                )
                if label_el:
                    label_text = await label_el.text_content()
                    if label_text:
                        label = label_text.strip()

            # Skip hidden and submit buttons
            if field_type in ["hidden", "submit", "button", "reset"]:
                return None

            # Get options for select elements
            options = []
            tag_name = await element.evaluate("(el) => el.tagName.toLowerCase()")
            if tag_name == "select":
                option_elements = await element.query_selector_all("option")
                for opt in option_elements:
                    opt_text = await opt.text_content()
                    if opt_text:
                        options.append(opt_text.strip())

            selector = f"#{field_id}" if field_id else f"[name='{name}']"

            return FormField(
                field_type=field_type,
                name=name or field_id,
                label=label,
                required=required,
                selector=selector,
                options=options
            )

        except Exception:
            return None

    async def _detect_with_ats_map(self, page, task_context, ats_type: str) -> int:
        """
        Detect form fields using ATS-specific mapping.

        Args:
            page: Playwright page object
            task_context: TaskContext object
            ats_type: ATS platform type

        Returns:
            Number of fields found using ATS mapping
        """
        from src.ai.field_maps import get_field_map, find_field_by_map, get_common_field_names
        from src.ai.task_context import FormField

        field_map = get_field_map(ats_type)
        fields_found = 0

        for field_name in get_common_field_names():
            try:
                element = await find_field_by_map(page, field_name, field_map)
                if element:
                    field_info = await self._extract_field_info(element)
                    if field_info:
                        # Mark as ATS-detected
                        field_info.metadata = {"ats_detected": True, "field_name": field_name}
                        task_context.detected_fields.append(field_info)
                        fields_found += 1
            except Exception:
                continue

        return fields_found


class RecoveryAgent(BaseAgent):
    """Agent specialized in handling failures and recovery strategies."""

    async def handle_failure(self, task_context, page, failure_reason: str) -> dict:
        """
        Handle application failures with intelligent recovery strategies.

        Args:
            task_context: TaskContext object
            page: Playwright page object
            failure_reason: Reason for failure

        Returns:
            Recovery result with next action
        """
        from src.ai.task_context import AgentType, TaskStatus
        from src.core.logger import log

        task_context.add_attempt(
            AgentType.RECOVERY,
            f"handle_{failure_reason}",
            "started"
        )

        # Classify error type and apply specific strategy
        error_type = self._classify_error(failure_reason, task_context)
        log(f"[Recovery] Classified error: {error_type} from reason: {failure_reason}")

        # Check if we can retry
        if not task_context.can_retry() and error_type not in ["auth_required", "captcha_detected"]:
            task_context.set_status(TaskStatus.FAILED)
            task_context.add_attempt(
                AgentType.RECOVERY,
                f"handle_{failure_reason}",
                "max_retries_reached"
            )
            return {
                "success": False,
                "reason": "max_retries_reached",
                "action": "skip"
            }

        # Handle specific error types with targeted strategies
        if error_type == "auth_required":
            return await self._handle_auth_required(task_context, page)
        elif error_type == "captcha_detected":
            return await self._handle_captcha(task_context, page)
        elif error_type == "missing_fields":
            return await self._handle_missing_fields(task_context, page)
        elif error_type == "validation_error":
            return await self._handle_validation_error(task_context, page)
        elif error_type == "no_forms_found":
            return await self._handle_no_forms(task_context, page)
        elif error_type == "submission_failed":
            return await self._handle_submission_failure(task_context, page)
        elif error_type == "network_error":
            return await self._handle_network_error(task_context, page)
        else:
            return await self._handle_generic_failure(task_context, page)

    def _classify_error(self, failure_reason: str, task_context) -> str:
        """
        Classify error type for targeted recovery.

        Args:
            failure_reason: Raw failure reason
            task_context: TaskContext object

        Returns:
            Classified error type
        """
        reason_lower = failure_reason.lower()

        # Check for specific error patterns
        if "auth" in reason_lower or "login" in reason_lower:
            return "auth_required"
        elif "captcha" in reason_lower:
            return "captcha_detected"
        elif "missing" in reason_lower or "required field" in reason_lower:
            return "missing_fields"
        elif "validation" in reason_lower or "invalid" in reason_lower:
            return "validation_error"
        elif "no_forms" in reason_lower or "form" in reason_lower:
            return "no_forms_found"
        elif "submission" in reason_lower or "submit" in reason_lower:
            return "submission_failed"
        elif "timeout" in reason_lower or "network" in reason_lower:
            return "network_error"
        else:
            return "generic_failure"

    async def _handle_auth_required(self, task_context, page) -> dict:
        """Handle authentication requirement."""
        from src.ai.task_context import AgentType, TaskStatus

        task_context.add_attempt(
            AgentType.RECOVERY,
            "handle_auth_required",
            "checking_session"
        )

        # Check if we have a saved session for this platform
        # This would integrate with existing session_manager
        task_context.set_status(TaskStatus.NEEDS_REVIEW)

        return {
            "success": False,
            "reason": "auth_required",
            "action": "needs_manual_login",
            "message": "Authentication required. Please log in manually."
        }

    async def _handle_captcha(self, task_context, page) -> dict:
        """Handle CAPTCHA detection."""
        from src.ai.task_context import AgentType, TaskStatus

        task_context.captcha_detected = True
        task_context.set_status(TaskStatus.NEEDS_REVIEW)
        task_context.add_attempt(
            AgentType.RECOVERY,
            "handle_captcha",
            "manual_intervention_required"
        )

        return {
            "success": False,
            "reason": "captcha_detected",
            "action": "needs_manual_captcha",
            "message": "CAPTCHA detected. Manual intervention required."
        }

    async def _handle_no_forms(self, task_context, page) -> dict:
        """Handle case where no forms are found."""
        from src.ai.task_context import AgentType

        # Try to find apply buttons or links
        apply_buttons = await page.query_selector_all(
            "button:has-text('Apply'), a:has-text('Apply'), button:has-text('Submit Application')"
        )

        if apply_buttons:
            task_context.add_attempt(
                AgentType.RECOVERY,
                "handle_no_forms",
                "found_apply_button"
            )
            # Click the button and re-run form detection
            try:
                await apply_buttons[0].click()
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass

            return {
                "success": True,
                "reason": "found_apply_button",
                "action": "retry",
                "delegate_to": "form_detector"
            }

        task_context.add_attempt(
            AgentType.RECOVERY,
            "handle_no_forms",
            "no_recovery_possible"
        )

        return {
            "success": False,
            "reason": "no_forms_or_buttons",
            "action": "skip"
        }

    async def _handle_missing_fields(self, task_context, page) -> dict:
        """Handle missing required fields."""
        from src.ai.task_context import AgentType

        task_context.add_attempt(
            AgentType.RECOVERY,
            "handle_missing_fields",
            "re_running_detection"
        )

        # Re-run form detection with ATS mapping
        return {
            "success": True,
            "reason": "retry_with_ats_mapping",
            "action": "retry",
            "delegate_to": "form_detector"
        }

    async def _handle_validation_error(self, task_context, page) -> dict:
        """Handle validation errors."""
        from src.ai.task_context import AgentType

        # Check for specific validation messages
        error_messages = []
        try:
            error_elements = await page.query_selector_all(".error, .validation-error, [role='alert']")
            for elem in error_elements:
                text = await elem.text_content()
                if text:
                    error_messages.append(text.strip())
        except Exception:
            pass

        task_context.add_attempt(
            AgentType.RECOVERY,
            "handle_validation_error",
            "detected_validation_errors",
            metadata={"errors": error_messages[:3]}
        )

        if task_context.can_retry():
            task_context.increment_retry()
            return {
                "success": True,
                "reason": "retry_after_validation_error",
                "action": "retry",
                "delegate_to": "form_filler"
            }

        return {
            "success": False,
            "reason": "validation_error_max_retries",
            "action": "skip"
        }

    async def _handle_network_error(self, task_context, page) -> dict:
        """Handle network/timeout errors."""
        from src.ai.task_context import AgentType
        import asyncio

        task_context.add_attempt(
            AgentType.RECOVERY,
            "handle_network_error",
            "waiting_before_retry"
        )

        if task_context.can_retry():
            # Wait before retry
            await asyncio.sleep(3)
            task_context.increment_retry()
            return {
                "success": True,
                "reason": "retry_after_network_error",
                "action": "retry",
                "delegate_to": "navigator"
            }

        return {
            "success": False,
            "reason": "network_error_max_retries",
            "action": "skip"
        }

    async def _handle_submission_failure(self, task_context, page) -> dict:
        """Handle form submission failure."""
        from src.ai.task_context import AgentType

        if task_context.can_retry():
            task_context.increment_retry()
            task_context.add_attempt(
                AgentType.RECOVERY,
                "handle_submission_failure",
                "retrying"
            )
            return {
                "success": True,
                "reason": "retry_submission",
                "action": "retry",
                "delegate_to": "form_filler"
            }

        return {
            "success": False,
            "reason": "submission_failed_max_retries",
            "action": "skip"
        }

    async def _handle_generic_failure(self, task_context, page) -> dict:
        """Handle generic failures."""
        from src.ai.task_context import AgentType

        if task_context.can_retry():
            task_context.increment_retry()
            task_context.add_attempt(
                AgentType.RECOVERY,
                "handle_generic_failure",
                "retrying"
            )
            return {
                "success": True,
                "reason": "retry_generic",
                "action": "retry",
                "delegate_to": "navigator"
            }

        return {
            "success": False,
            "reason": "generic_failure_max_retries",
            "action": "skip"
        }


class AgentOrchestrator:
    """Orchestrates multiple agents to handle job application workflow."""

    def __init__(self, profile: dict, settings: dict):
        self.evaluator = JobEvaluatorAgent(profile, settings)
        self.applicator = ApplicationAgent(profile, settings)
        self.reviewer = ReviewAgent(profile, settings)
        self.strategist = StrategyAgent(profile, settings)
        self.navigator = NavigationAgent(profile, settings)
        self.form_detector = FormDetectionAgent(profile, settings)
        self.recovery = RecoveryAgent(profile, settings)
        self.profile = profile
        self.settings = settings

    async def execute_application(self, task_context, page) -> dict:
        """
        Execute full application flow with agent coordination.

        This is the main entry point for coordinated multi-agent application.

        Args:
            task_context: TaskContext object
            page: Playwright page object

        Returns:
            Final application result
        """
        from src.ai.task_context import TaskStatus, AgentType
        from src.core.logger import log

        log(f"[Orchestrator] Starting application for job {task_context.job_key}")
        task_context.set_status(TaskStatus.IN_PROGRESS)

        # Step 1: Navigate to apply URL
        nav_result = await self.navigator.handle_navigation(task_context, page)
        log(f"[Orchestrator] Navigation result: {nav_result.get('success')}")

        if not nav_result["success"]:
            return await self._delegate_to_recovery(
                task_context, page, nav_result.get("reason", "navigation_failed")
            )

        # Step 2: Detect forms
        if nav_result.get("delegate_to") == "form_detector":
            form_result = await self.form_detector.detect_form(task_context, page)
            log(f"[Orchestrator] Form detection result: {form_result.get('success')}")

            if not form_result["success"]:
                return await self._delegate_to_recovery(
                    task_context, page, form_result.get("reason", "form_detection_failed")
                )

            # Step 3: Fill form
            if form_result.get("delegate_to") == "form_filler":
                fill_result = await self._fill_form(task_context, page)
                log(f"[Orchestrator] Form fill result: {fill_result.get('success')}")

                if not fill_result["success"]:
                    return await self._delegate_to_recovery(
                        task_context, page, "submission_failed"
                    )

                task_context.submission_successful = True
                task_context.set_status(TaskStatus.COMPLETED)
                log(f"[Orchestrator] Application completed successfully for {task_context.job_key}")

                return {
                    "success": True,
                    "status": "completed",
                    "task_context": task_context.to_dict()
                }

        # Fallback
        task_context.set_status(TaskStatus.FAILED)
        return {
            "success": False,
            "status": "failed",
            "reason": "unexpected_flow",
            "task_context": task_context.to_dict()
        }

    async def _delegate_to_recovery(self, task_context, page, failure_reason: str) -> dict:
        """Delegate to recovery agent."""
        from src.core.logger import log

        log(f"[Orchestrator] Delegating to recovery agent: {failure_reason}")

        recovery_result = await self.recovery.handle_failure(task_context, page, failure_reason)

        if recovery_result.get("action") == "retry":
            # Retry based on delegate_to
            delegate_to = recovery_result.get("delegate_to")
            if delegate_to == "navigator":
                return await self.execute_application(task_context, page)
            elif delegate_to == "form_filler":
                return await self._fill_form(task_context, page)

        # Recovery failed or requires manual intervention
        return {
            "success": False,
            "status": "failed",
            "reason": recovery_result.get("reason"),
            "action": recovery_result.get("action"),
            "message": recovery_result.get("message"),
            "task_context": task_context.to_dict()
        }

    async def _fill_form(self, task_context, page) -> dict:
        """Fill form using existing form_filler module."""
        from src.ai.task_context import AgentType
        from src.ai.form_filler import fill_application_form
        from src.core.logger import log

        task_context.add_attempt(
            AgentType.FORM_FILLER,
            "fill_application_form",
            "started"
        )

        try:
            # Build job dict for form_filler
            job = {
                "title": task_context.metadata.get("title"),
                "company": task_context.metadata.get("company"),
                "location": task_context.metadata.get("location"),
            }

            # Use existing form_filler
            result = await fill_application_form(
                page,
                self.profile,
                job,
                task_context.platform
            )

            filled_count = result.get("filled_count", 0)
            unresolved = result.get("unresolved_prompts", [])

            task_context.filled_fields = result.get("filled_prompts", [])
            task_context.missing_fields = unresolved

            if unresolved:
                log(f"[Orchestrator] Unresolved fields: {unresolved}")

            task_context.add_attempt(
                AgentType.FORM_FILLER,
                "fill_application_form",
                "success",
                metadata={
                    "filled_count": filled_count,
                    "unresolved_count": len(unresolved)
                }
            )

            # Try to submit
            submit_result = await self._submit_form(task_context, page)

            return submit_result

        except Exception as exc:
            task_context.add_error(f"Form filling failed: {exc}")
            task_context.add_attempt(
                AgentType.FORM_FILLER,
                "fill_application_form",
                "failed",
                error=str(exc)
            )
            return {
                "success": False,
                "reason": "form_fill_error",
                "error": str(exc)
            }

    async def _submit_form(self, task_context, page) -> dict:
        """Submit the application form with verification."""
        from src.ai.task_context import AgentType
        from src.ai.verification import verify_submission
        from src.ai.human_behavior import add_human_delay
        from src.core.logger import log

        task_context.add_attempt(
            AgentType.FORM_FILLER,
            "submit_form",
            "started"
        )

        try:
            # Add human-like delay before submitting
            await add_human_delay("button_click")

            # Find submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Send Application')",
            ]

            submit_button = None
            for selector in submit_selectors:
                submit_button = await page.query_selector(selector)
                if submit_button:
                    break

            if not submit_button:
                task_context.add_error("Submit button not found")
                task_context.add_attempt(
                    AgentType.FORM_FILLER,
                    "submit_form",
                    "failed",
                    error="submit_button_not_found"
                )
                return {
                    "success": False,
                    "reason": "submit_button_not_found"
                }

            # Click submit
            await submit_button.click()
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Verify submission using verification module
            verification_result = await verify_submission(page, task_context)
            log(f"[Orchestrator] Verification result: {verification_result['status']} (confidence: {verification_result['confidence']}%)")

            if verification_result["status"] == "success":
                task_context.confirmation_message = ", ".join(verification_result["evidence"])
                task_context.add_attempt(
                    AgentType.FORM_FILLER,
                    "submit_form",
                    "success",
                    metadata={"verification": verification_result}
                )
                return {
                    "success": True,
                    "confirmation": task_context.confirmation_message,
                    "verification": verification_result
                }
            elif verification_result["status"] == "failed":
                task_context.add_error(f"Submission failed: {verification_result['error_messages']}")
                task_context.add_attempt(
                    AgentType.FORM_FILLER,
                    "submit_form",
                    "failed",
                    error="verification_failed",
                    metadata={"verification": verification_result}
                )
                return {
                    "success": False,
                    "reason": "submission_failed",
                    "error_messages": verification_result["error_messages"],
                    "verification": verification_result
                }
            else:  # uncertain
                log(f"[Orchestrator] Submission verification uncertain - marking for review")
                task_context.add_attempt(
                    AgentType.FORM_FILLER,
                    "submit_form",
                    "uncertain",
                    metadata={"verification": verification_result}
                )
                return {
                    "success": True,  # Assume success but flag for review
                    "confirmation": "Submission status uncertain - needs review",
                    "verification": verification_result,
                    "needs_review": True
                }
                    confirmation_text = await element.text_content()
                    task_context.confirmation_message = confirmation_text
                    confirmation_found = True
                    break

            if confirmation_found:
                log(f"[Orchestrator] Application submitted successfully")
                task_context.add_attempt(
                    AgentType.FORM_FILLER,
                    "submit_form",
                    "success"
                )
                return {
                    "success": True,
                    "confirmation": task_context.confirmation_message
                }
            else:
                # Assume success if no error
                log(f"[Orchestrator] Form submitted (no explicit confirmation)")
                task_context.add_attempt(
                    AgentType.FORM_FILLER,
                    "submit_form",
                    "success_assumed"
                )
                return {
                    "success": True,
                    "confirmation": "Form submitted (no confirmation message)"
                }

        except Exception as exc:
            task_context.add_error(f"Form submission failed: {exc}")
            task_context.add_attempt(
                AgentType.FORM_FILLER,
                "submit_form",
                "failed",
                error=str(exc)
            )
            return {
                "success": False,
                "reason": "submission_error",
                "error": str(exc)
            }

    def process_job(self, job: dict) -> dict:
        """
        Process a single job through the agent pipeline.

        Returns:
            Complete decision with all agent outputs
        """
        # Step 1: Evaluate the job
        evaluation = self.evaluator.evaluate(job)

        # Step 2: If needs review, get review analysis
        review_analysis = None
        if evaluation.get("confused") or evaluation.get("decision") == "REVIEW":
            review_analysis = self.reviewer.analyze_for_review(job, evaluation)

        # Step 3: Plan application strategy
        application_plan = None
        if evaluation.get("apply"):
            application_plan = self.applicator.plan_application(job, evaluation)

        return {
            "evaluation": evaluation,
            "review_analysis": review_analysis,
            "application_plan": application_plan,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def process_batch(self, jobs: List[dict]) -> List[dict]:
        """
        Process multiple jobs and prioritize them.

        Returns:
            List of processed jobs with priorities
        """
        # Evaluate all jobs
        jobs_with_evaluations = []
        for job in jobs:
            evaluation = self.evaluator.evaluate(job)
            if evaluation.get("apply"):
                jobs_with_evaluations.append((job, evaluation))

        # Prioritize
        prioritized = self.strategist.prioritize_batch(jobs_with_evaluations)

        # Add application plans
        for item in prioritized:
            item["application_plan"] = self.applicator.plan_application(
                item["job"], item["evaluation"]
            )

        return prioritized


def create_orchestrator(profile: dict, settings: dict) -> AgentOrchestrator:
    """Factory function to create orchestrator."""
    return AgentOrchestrator(profile, settings)

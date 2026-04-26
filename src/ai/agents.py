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


class AgentOrchestrator:
    """Orchestrates multiple agents to handle job application workflow."""

    def __init__(self, profile: dict, settings: dict):
        self.evaluator = JobEvaluatorAgent(profile, settings)
        self.applicator = ApplicationAgent(profile, settings)
        self.reviewer = ReviewAgent(profile, settings)
        self.strategist = StrategyAgent(profile, settings)

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

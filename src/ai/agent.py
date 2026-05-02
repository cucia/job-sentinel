"""
AI Agent for intelligent job evaluation and decision making.

This agent replaces simple scoring with a reasoning-based approach that:
- Analyzes job descriptions deeply
- Makes autonomous decisions about applications
- Provides detailed reasoning for decisions
- Learns from user feedback
- Handles edge cases intelligently
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from src.ai.cloud_llm import create_llm_client


class JobAgent:
    """Intelligent agent for job evaluation and application decisions."""

    def __init__(self, profile: dict, settings: dict):
        self.profile = profile
        self.settings = settings
        self.client = create_llm_client(settings)
        self.min_score = settings.get("ai", {}).get("min_score", 70)
        self.conversation_history: List[dict] = []

    def evaluate_job(self, job: dict, context: Optional[dict] = None) -> dict:
        """
        Evaluate a job using AI reasoning.

        Args:
            job: Job details (title, company, description, etc.)
            context: Additional context (recent applications, feedback, etc.)

        Returns:
            Decision dict with action, reasoning, confidence, etc.
        """
        prompt = self._build_evaluation_prompt(job, context)

        try:
            response = self.client.chat(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )

            decision = self._parse_agent_response(response, job)
            self._log_decision(job, decision)
            return decision

        except Exception as exc:
            return self._fallback_decision(job, str(exc))

    def _get_system_prompt(self) -> str:
        """Build the system prompt that defines agent behavior."""
        skills = ", ".join(self.profile.get("skills", [])[:8])
        keywords = ", ".join(self.profile.get("keywords", [])[:8])
        role = self.profile.get("role", "cybersecurity professional")
        experience = self.profile.get("experience", "entry-level")
        location = self.profile.get("location", "")

        return f"""You are an intelligent job application agent helping a candidate find the right opportunities.

CANDIDATE PROFILE:
- Target Role: {role}
- Experience Level: {experience}
- Core Skills: {skills}
- Target Keywords: {keywords}
- Preferred Location: {location}

YOUR MISSION:
Analyze job postings and make smart decisions about whether to apply. You should:
1. Deeply understand job requirements vs candidate qualifications
2. Identify red flags (unrealistic requirements, mismatches)
3. Spot opportunities (growth potential, skill matches)
4. Make confident decisions with clear reasoning

DECISION FRAMEWORK:
- APPLY: Strong match, candidate qualifies, worth pursuing
- REJECT: Clear mismatch, overqualified/underqualified, or red flags
- REVIEW: Uncertain, need human judgment, or borderline case

Be decisive but honest. Don't apply to jobs where the candidate clearly doesn't fit.
Prioritize quality over quantity - better to apply to 10 good matches than 100 poor ones."""

    def _build_evaluation_prompt(self, job: dict, context: Optional[dict]) -> str:
        """Build the evaluation prompt for a specific job."""
        job_info = f"""
JOB POSTING:
Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}
Platform: {job.get('platform', 'N/A')}
Easy Apply: {'Yes' if job.get('easy_apply') else 'No'}
Posted: {job.get('posted_text', job.get('posted_at', 'N/A'))}
"""

        if job.get('description'):
            desc = job.get('description', '')[:3000]
            job_info += f"\nDescription:\n{desc}"

        context_info = ""
        if context:
            if context.get('recent_applications'):
                context_info += f"\nRecent applications today: {context['recent_applications']}"
            if context.get('feedback_summary'):
                context_info += f"\nRecent feedback: {context['feedback_summary']}"

        return f"""{job_info}
{context_info}

TASK:
Analyze this job posting and decide whether the candidate should apply.

Respond in this EXACT format:
DECISION: <APPLY|REJECT|REVIEW>
CONFIDENCE: <0-100>
SCORE: <0-100>
REASONING: <2-3 sentences explaining your decision>
KEY_FACTORS: <comma-separated list of 3-5 key factors>
RED_FLAGS: <comma-separated list of concerns, or "none">
OPPORTUNITIES: <comma-separated list of positives, or "none">

Be specific and actionable in your reasoning."""

    def _parse_agent_response(self, response: str, job: dict) -> dict:
        """Parse the agent's structured response."""
        decision = "REVIEW"
        confidence = 50
        score = 50
        reasoning = "Agent evaluation completed"
        key_factors = []
        red_flags = []
        opportunities = []

        for line in response.split("\n"):
            line = line.strip()

            if line.startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip().upper()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = int(re.search(r'\d+', line.split(":", 1)[1]).group())
                except (ValueError, AttributeError):
                    pass
            elif line.startswith("SCORE:"):
                try:
                    score = int(re.search(r'\d+', line.split(":", 1)[1]).group())
                except (ValueError, AttributeError):
                    pass
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
            elif line.startswith("KEY_FACTORS:"):
                factors_text = line.split(":", 1)[1].strip()
                if factors_text.lower() != "none":
                    key_factors = [f.strip() for f in factors_text.split(",")]
            elif line.startswith("RED_FLAGS:"):
                flags_text = line.split(":", 1)[1].strip()
                if flags_text.lower() != "none":
                    red_flags = [f.strip() for f in flags_text.split(",")]
            elif line.startswith("OPPORTUNITIES:"):
                opps_text = line.split(":", 1)[1].strip()
                if opps_text.lower() != "none":
                    opportunities = [o.strip() for o in opps_text.split(",")]

        apply = decision == "APPLY" and score >= self.min_score and confidence >= 60
        confused = decision == "REVIEW" or confidence < 60 or abs(score - self.min_score) <= 10

        priority_score = score
        if job.get("easy_apply"):
            priority_score += 8
        if "fresh" in " ".join(key_factors).lower():
            priority_score += 5

        return {
            "apply": apply,
            "confused": confused,
            "score": score,
            "confidence": confidence,
            "priority_score": min(100, priority_score),
            "decision": decision,
            "reasoning": reasoning,
            "key_factors": key_factors[:5],
            "red_flags": red_flags[:5],
            "opportunities": opportunities[:5],
            "agent_version": "v1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _fallback_decision(self, job: dict, error: str) -> dict:
        """Fallback decision when agent fails."""
        return {
            "apply": False,
            "confused": True,
            "score": 0,
            "confidence": 0,
            "priority_score": 0,
            "decision": "REVIEW",
            "reasoning": f"Agent evaluation failed: {error}",
            "key_factors": [],
            "red_flags": ["agent_error"],
            "opportunities": [],
            "agent_version": "v1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _log_decision(self, job: dict, decision: dict) -> None:
        """Log the decision for debugging and learning."""
        self.conversation_history.append({
            "job_key": job.get("job_key"),
            "title": job.get("title"),
            "decision": decision,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def learn_from_feedback(self, job: dict, feedback: str, outcome: str) -> dict:
        """
        Learn from user feedback on a decision.

        Args:
            job: The job that was evaluated
            feedback: User's feedback (approved/rejected)
            outcome: What happened (applied/skipped/etc)

        Returns:
            Learning summary
        """
        prompt = f"""
FEEDBACK RECEIVED:
Job: {job.get('title')} at {job.get('company')}
Your Decision: {job.get('decision', 'unknown')}
User Feedback: {feedback}
Outcome: {outcome}

TASK:
Analyze what you can learn from this feedback. What should you adjust in future evaluations?

Respond with:
LESSON: <one sentence key takeaway>
ADJUSTMENT: <what to change in future decisions>
"""

        try:
            response = self.client.chat(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            lesson = ""
            adjustment = ""
            for line in response.split("\n"):
                if line.startswith("LESSON:"):
                    lesson = line.split(":", 1)[1].strip()
                elif line.startswith("ADJUSTMENT:"):
                    adjustment = line.split(":", 1)[1].strip()

            return {
                "lesson": lesson,
                "adjustment": adjustment,
                "feedback": feedback,
                "outcome": outcome,
            }
        except Exception as exc:
            return {
                "lesson": "Failed to process feedback",
                "adjustment": "",
                "error": str(exc),
            }

    def batch_evaluate(self, jobs: List[dict], context: Optional[dict] = None) -> List[Tuple[dict, dict]]:
        """
        Evaluate multiple jobs in batch.

        Args:
            jobs: List of job dicts
            context: Shared context for all evaluations

        Returns:
            List of (job, decision) tuples
        """
        results = []
        for job in jobs:
            decision = self.evaluate_job(job, context)
            results.append((job, decision))
        return results

    def explain_decision(self, job: dict, decision: dict) -> str:
        """
        Generate a human-readable explanation of a decision.

        Args:
            job: The job that was evaluated
            decision: The decision dict

        Returns:
            Human-readable explanation
        """
        action = decision.get("decision", "REVIEW")
        score = decision.get("score", 0)
        confidence = decision.get("confidence", 0)
        reasoning = decision.get("reasoning", "No reasoning provided")

        explanation = f"**Decision: {action}** (Score: {score}/100, Confidence: {confidence}%)\n\n"
        explanation += f"{reasoning}\n\n"

        if decision.get("key_factors"):
            explanation += f"**Key Factors:** {', '.join(decision['key_factors'])}\n\n"

        if decision.get("opportunities"):
            explanation += f"**Opportunities:** {', '.join(decision['opportunities'])}\n\n"

        if decision.get("red_flags"):
            explanation += f"**Red Flags:** {', '.join(decision['red_flags'])}\n\n"

        return explanation


def create_agent(profile: dict, settings: dict) -> JobAgent:
    """Factory function to create a configured agent."""
    return JobAgent(profile, settings)

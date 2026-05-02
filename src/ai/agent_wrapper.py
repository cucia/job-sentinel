"""
Agent-based evaluation wrapper for backward compatibility.

This module provides a bridge between the new AI agent and the existing scorer interface.
"""

from src.ai.agent import create_agent
from src.ai.scorer import evaluate_job as heuristic_evaluate_job


def evaluate_job_with_agent(
    job: dict,
    profile: dict,
    settings: dict,
    context: dict | None = None,
) -> dict:
    """
    Evaluate a job using the AI agent.

    Args:
        job: Job details
        profile: Candidate profile
        settings: Application settings
        context: Additional context (recent applications, feedback, etc.)

    Returns:
        Decision dict compatible with existing code
    """
    use_agent = settings.get("ai", {}).get("use_agent", False)

    if not use_agent:
        min_score = settings.get("ai", {}).get("min_score", 70)
        uncertainty_margin = settings.get("ai", {}).get("uncertainty_margin", 5)
        return heuristic_evaluate_job(
            job, profile, min_score, uncertainty_margin, model_state=None
        )

    # Use the AI agent
    agent = create_agent(profile, settings)
    decision = agent.evaluate_job(job, context)

    # Add backward-compatible fields
    decision["heuristic_score"] = decision.get("score", 0)
    decision["learned_adjustment"] = 0
    decision["matched_terms"] = decision.get("key_factors", [])
    decision["signals"] = []
    decision["trained_examples"] = 0

    return decision


def learn_from_feedback_with_agent(
    job: dict,
    profile: dict,
    settings: dict,
    feedback: str,
    outcome: str,
) -> dict:
    """
    Process user feedback through the agent.

    Args:
        job: The job that was evaluated
        profile: Candidate profile
        settings: Application settings
        feedback: User's feedback (approved/rejected)
        outcome: What happened (applied/skipped/etc)

    Returns:
        Learning summary
    """
    use_agent = settings.get("ai", {}).get("use_agent", False)

    if not use_agent:
        return {"lesson": "Agent not enabled", "adjustment": ""}

    agent = create_agent(profile, settings)
    return agent.learn_from_feedback(job, feedback, outcome)

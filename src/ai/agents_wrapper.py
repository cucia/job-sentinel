"""
Multi-Agent wrapper for backward compatibility with existing controller code.
"""

from src.ai.agents import AgentOrchestrator
from src.ai.scorer import evaluate_job as heuristic_evaluate_job


def evaluate_job_with_agents(
    job: dict,
    profile: dict,
    settings: dict,
) -> dict:
    """
    Evaluate a job using the multi-agent system.

    Args:
        job: Job details
        profile: Candidate profile
        settings: Application settings

    Returns:
        Decision dict compatible with existing controller code
    """
    use_agents = settings.get("ai", {}).get("use_agents", False)
    use_cloud = settings.get("ai", {}).get("use_cloud", False)

    if not use_agents or not use_cloud:
        min_score = settings.get("ai", {}).get("min_score", 70)
        uncertainty_margin = settings.get("ai", {}).get("uncertainty_margin", 5)
        return heuristic_evaluate_job(
            job, profile, min_score, uncertainty_margin, model_state=None
        )

    # Use the multi-agent system
    orchestrator = AgentOrchestrator(profile, settings)
    result = orchestrator.process_job(job)

    evaluation = result.get("evaluation", {})
    application_plan = result.get("application_plan", {})
    review_analysis = result.get("review_analysis", {})

    # Build backward-compatible response
    decision = {
        "apply": evaluation.get("apply", False),
        "confused": evaluation.get("confused", False),
        "score": evaluation.get("score", 0),
        "confidence": evaluation.get("confidence", 0),
        "priority_score": evaluation.get("priority_score", 0),
        "decision": evaluation.get("decision", "REVIEW"),
        "agent_registry": result.get("agent_registry", []),

        # Agent-specific fields
        "reasoning": evaluation.get("reasoning", ""),
        "match_factors": evaluation.get("match_factors", []),
        "concerns": evaluation.get("concerns", []),

        # Application strategy
        "application_strategy": application_plan.get("strategy") if application_plan else None,
        "application_priority": application_plan.get("priority") if application_plan else None,

        # Review info
        "review_reason": review_analysis.get("review_reason") if review_analysis else None,
        "review_questions": review_analysis.get("questions") if review_analysis else None,

        # Backward compatibility fields
        "heuristic_score": evaluation.get("score", 0),
        "learned_adjustment": 0,
        "matched_terms": evaluation.get("match_factors", []),
        "signals": [],
        "trained_examples": 0,

        # Agent metadata
        "agent_version": "multi-agent-v1.0",
        "agents_used": [
            agent.get("display_name")
            for agent in result.get("agent_registry", [])
            if agent.get("enabled") and agent.get("stage") == "evaluation"
        ] or ["JobEvaluatorAgent", "ApplicationAgent", "ReviewAgent"],
    }

    return decision

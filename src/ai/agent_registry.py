from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


_AGENT_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "evaluator",
        "class_name": "JobEvaluatorAgent",
        "display_name": "JobEvaluatorAgent",
        "duty": "Evaluates job matches against the candidate profile.",
        "required": False,
        "fallback": "heuristic_evaluation",
        "default_enabled": True,
        "stage": "evaluation",
    },
    {
        "id": "application",
        "class_name": "ApplicationAgent",
        "display_name": "ApplicationAgent",
        "duty": "Plans how and when an application should be attempted.",
        "required": False,
        "fallback": "score_based_planning",
        "default_enabled": True,
        "stage": "evaluation",
    },
    {
        "id": "review",
        "class_name": "ReviewAgent",
        "display_name": "ReviewAgent",
        "duty": "Explains borderline decisions that should be reviewed by a human.",
        "required": False,
        "fallback": "keep_review_without_analysis",
        "default_enabled": True,
        "stage": "evaluation",
    },
    {
        "id": "strategy",
        "class_name": "StrategyAgent",
        "display_name": "StrategyAgent",
        "duty": "Prioritizes promising jobs for faster application throughput.",
        "required": False,
        "fallback": "score_based_ordering",
        "default_enabled": True,
        "stage": "evaluation",
    },
    {
        "id": "navigator",
        "class_name": "NavigationAgent",
        "display_name": "NavigationAgent",
        "duty": "Navigates to the target application flow and checks prerequisites.",
        "required": True,
        "fallback": "review_required",
        "default_enabled": True,
        "stage": "application",
    },
    {
        "id": "form_detector",
        "class_name": "FormDetectionAgent",
        "display_name": "FormDetectionAgent",
        "duty": "Detects the application form and the fields that must be completed.",
        "required": True,
        "fallback": "review_required",
        "default_enabled": True,
        "stage": "application",
    },
    {
        "id": "form_filler",
        "class_name": "FormFillerAgent",
        "display_name": "FormFillerAgent",
        "duty": "Completes detected fields and submits the application form.",
        "required": True,
        "fallback": "review_required",
        "default_enabled": True,
        "stage": "application",
    },
    {
        "id": "recovery",
        "class_name": "RecoveryAgent",
        "display_name": "RecoveryAgent",
        "duty": "Handles failures, retries, and escalation when the workflow breaks.",
        "required": False,
        "fallback": "fail_fast_to_review",
        "default_enabled": True,
        "stage": "application",
    },
]

_AGENT_BY_ID = {agent["id"]: agent for agent in _AGENT_DEFINITIONS}
_AGENT_BY_CLASS = {agent["class_name"]: agent for agent in _AGENT_DEFINITIONS}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _controls(settings: dict) -> dict:
    return settings.setdefault("ai", {}).setdefault("agent_controls", {})


def agent_definitions() -> List[Dict[str, Any]]:
    return [deepcopy(agent) for agent in _AGENT_DEFINITIONS]


def get_agent_definition(agent_id: Optional[str] = None, *, class_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if agent_id:
        agent = _AGENT_BY_ID.get(agent_id)
    elif class_name:
        agent = _AGENT_BY_CLASS.get(class_name)
    else:
        agent = None
    return deepcopy(agent) if agent else None


def ensure_agent_controls(settings: dict) -> dict:
    controls = _controls(settings)
    for definition in _AGENT_DEFINITIONS:
        state = controls.setdefault(definition["id"], {})
        state.setdefault("enabled", definition["default_enabled"])
    return controls


def set_agent_enabled(settings: dict, agent_id: str, enabled: bool) -> dict:
    controls = ensure_agent_controls(settings)
    state = controls.setdefault(agent_id, {})
    state["enabled"] = bool(enabled)
    state["updated_at"] = _now_iso()
    return state


def is_agent_enabled(settings: dict, agent_id: str) -> bool:
    definition = _AGENT_BY_ID.get(agent_id)
    default_enabled = definition["default_enabled"] if definition else True
    controls = ensure_agent_controls(settings)
    return bool(controls.get(agent_id, {}).get("enabled", default_enabled))


def build_agent_registry(settings: dict, runtime_statuses: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    runtime_statuses = runtime_statuses or {}
    controls = ensure_agent_controls(settings)
    agents = []

    for definition in _AGENT_DEFINITIONS:
        agent_id = definition["id"]
        control = controls.get(agent_id, {})
        runtime = runtime_statuses.get(agent_id, {})
        enabled = bool(control.get("enabled", definition["default_enabled"]))
        status = runtime.get("status") or ("idle" if enabled else "disabled")
        agents.append({
            **deepcopy(definition),
            "enabled": enabled,
            "status": status,
            "last_seen": runtime.get("last_seen") or control.get("updated_at"),
            "last_event": runtime.get("last_event"),
            "reason": runtime.get("reason"),
        })

    return agents


def runtime_status_map(agents: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    statuses: Dict[str, Dict[str, Any]] = {}
    for agent in agents:
        statuses[agent["id"]] = {
            "status": agent.get("status"),
            "last_seen": agent.get("last_seen"),
            "last_event": agent.get("last_event"),
            "reason": agent.get("reason"),
            "enabled": agent.get("enabled"),
        }
    return statuses

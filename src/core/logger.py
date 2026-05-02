import datetime
import os
from typing import Any, Dict, Optional


_socketio_instance = None
_AGENT_EVENTS: list[dict[str, Any]] = []
_MAX_AGENT_EVENTS = 200


def set_socketio(socketio):
    """Set the SocketIO instance for real-time broadcasting."""
    global _socketio_instance
    _socketio_instance = socketio


def _log_path() -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "jobsentinel.log")


def _remember_agent_event(event: dict[str, Any]) -> None:
    _AGENT_EVENTS.append(event)
    if len(_AGENT_EVENTS) > _MAX_AGENT_EVENTS:
        del _AGENT_EVENTS[:-_MAX_AGENT_EVENTS]


def get_recent_agent_events(limit: int = 100) -> list[dict[str, Any]]:
    if limit <= 0:
        return list(_AGENT_EVENTS)
    return list(_AGENT_EVENTS[-limit:])


def emit_agent_event(
    event_type: str,
    *,
    agent: Optional[str] = None,
    target_agent: Optional[str] = None,
    job_key: Optional[str] = None,
    job_title: Optional[str] = None,
    status: Optional[str] = None,
    reason: Optional[str] = None,
    level: str = "info",
    metadata: Optional[Dict[str, Any]] = None,
) -> dict[str, Any]:
    timestamp = datetime.datetime.now().isoformat()
    event = {
        "timestamp": timestamp,
        "event_type": event_type,
        "agent": agent,
        "target_agent": target_agent,
        "job_key": job_key,
        "job_title": job_title,
        "status": status,
        "reason": reason,
        "level": level,
        "metadata": metadata or {},
    }
    _remember_agent_event(event)

    if _socketio_instance:
        try:
            _socketio_instance.emit("agent_event", event)
        except Exception:
            pass

    return event


def log(message: str, level: str = "info", agent: str = None, job_title: str = None, event: Optional[Dict[str, Any]] = None) -> None:
    """
    Log message to file, console, and broadcast to dashboard.

    Args:
        message: Log message
        level: Log level (info, success, warning, error, debug)
        agent: Agent name (e.g., "JobEvaluatorAgent", "NavigationAgent")
        job_title: Job title being processed
    """
    timestamp = datetime.datetime.now()
    line = f"[{timestamp}] {message}"

    # Console output
    print(line, flush=True)

    # File output
    with open(_log_path(), "a", encoding="utf-8") as f:
        f.write(line + "\n")

    # Real-time broadcast to dashboard
    if _socketio_instance:
        try:
            _socketio_instance.emit('agent_log', {
                'timestamp': timestamp.isoformat(),
                'message': message,
                'level': level,
                'agent': agent,
                'job_title': job_title
            })
        except Exception:
            pass

    if event:
        emit_agent_event(
            event.get("event_type", "log"),
            agent=event.get("agent", agent),
            target_agent=event.get("target_agent"),
            job_key=event.get("job_key"),
            job_title=event.get("job_title", job_title),
            status=event.get("status"),
            reason=event.get("reason", message),
            level=event.get("level", level),
            metadata=event.get("metadata"),
        )


import json
import os
import re
from datetime import datetime, timezone

from src.ai.profile_store import save_profile
from src.core.config import load_profile


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _agent_log_path(base_dir: str) -> str:
    return os.path.join(base_dir, "data", "agent_log.jsonl")


def _append_log(base_dir: str, role: str, content: str) -> None:
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": content,
    }
    with open(_agent_log_path(base_dir), "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def _load_recent_log(base_dir: str, limit: int = 20) -> list[dict]:
    path = _agent_log_path(base_dir)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    recent = []
    for line in lines[-limit:]:
        try:
            recent.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return recent


def _extract_profile_updates(text: str) -> dict:
    updates: dict[str, object] = {}
    lowered = text.lower().strip()

    name_match = re.search(r"\bmy name is\s+([a-zA-Z0-9 _-]+)", lowered)
    if name_match:
        updates["name"] = name_match.group(1).strip().title()

    role_match = re.search(r"\b(i am|i'm|my role is)\s+([a-zA-Z0-9 _-]+)", lowered)
    if role_match:
        updates["role"] = role_match.group(2).strip()

    exp_match = re.search(r"\b(\d+)\s+(years|year|months|month)\b", lowered)
    if exp_match:
        updates["experience"] = f"{exp_match.group(1)} {exp_match.group(2)}"

    skills_match = re.search(r"\bskills?\s*:\s*(.+)$", text, re.IGNORECASE)
    if skills_match:
        skills = [s.strip() for s in re.split(r"[,\n]", skills_match.group(1)) if s.strip()]
        if skills:
            updates["skills"] = skills

    keywords_match = re.search(r"\b(keywords?|target roles?)\s*:\s*(.+)$", text, re.IGNORECASE)
    if keywords_match:
        keywords = [s.strip() for s in re.split(r"[,\n]", keywords_match.group(2)) if s.strip()]
        if keywords:
            updates["keywords"] = keywords

    location_match = re.search(r"\b(location|based in|i live in)\s+([a-zA-Z0-9 ,_-]+)", lowered)
    if location_match:
        updates["location"] = location_match.group(2).strip()

    email_match = re.search(r"\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b", text, re.IGNORECASE)
    if email_match:
        updates["email"] = email_match.group(1).strip()

    phone_match = re.search(r"(\+?\d[\d\s-]{7,}\d)", text)
    if phone_match:
        updates["phone"] = phone_match.group(1).strip()

    notice_match = re.search(r"\bnotice(?: period)?\s*[:=]?\s*(\d+)\s*(days|day)?\b", lowered)
    if notice_match:
        updates["notice_period_days"] = notice_match.group(1).strip()

    if "authorized to work" in lowered or "work authorization yes" in lowered:
        updates["work_authorization"] = True
    if "require sponsorship" in lowered:
        updates["sponsorship_required"] = True
    if "do not require sponsorship" in lowered or "no sponsorship" in lowered:
        updates["sponsorship_required"] = False
    if "willing to relocate" in lowered:
        updates["willing_to_relocate"] = True
    if "not willing to relocate" in lowered:
        updates["willing_to_relocate"] = False

    return updates


def _missing_fields(profile: dict) -> list[str]:
    missing = []
    for field in ("role", "experience", "skills", "location", "keywords", "email", "phone"):
        value = profile.get(field)
        if not value:
            missing.append(field)
    return missing


def _agent_reply(profile: dict, user_text: str) -> str:
    missing = _missing_fields(profile)
    if missing:
        prompt = "I need a few details to personalize matches. Please share: "
        prompt += ", ".join(missing)
        prompt += "."
        return prompt
    return "Got it. I'll use this profile to evaluate jobs and learn from your approvals and rejections."


def handle_chat(user_text: str, profile_name: str) -> dict:
    base_dir = _base_dir()
    profile = load_profile(base_dir, profile_name)
    updates = _extract_profile_updates(user_text)
    if updates:
        profile.update(updates)
        save_profile(base_dir, profile_name, profile)

    _append_log(base_dir, "user", user_text)
    reply = _agent_reply(profile, user_text)
    _append_log(base_dir, "assistant", reply)

    return {
        "reply": reply,
        "profile": profile,
        "messages": _load_recent_log(base_dir),
    }

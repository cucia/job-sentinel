import re
from datetime import datetime, timezone


POSITIVE_LABELS = {"approve", "approved", "applied", "positive", "accept", "accepted", "good"}
NEGATIVE_LABELS = {"reject", "rejected", "negative", "skip", "skipped", "decline", "bad"}


def _normalize_term(term: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (term or "").lower()))


def _unique_terms(terms: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for term in terms:
        normalized = _normalize_term(term)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _posted_minutes_ago(job: dict) -> int | None:
    posted_at = (job.get("posted_at") or "").strip()
    if posted_at:
        try:
            normalized = posted_at[:-1] + "+00:00" if posted_at.endswith("Z") else posted_at
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            minutes = int((datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() // 60)
            return max(0, minutes)
        except ValueError:
            pass

    posted_text = (job.get("posted_text") or "").strip().lower()
    if not posted_text:
        return None
    if any(token in posted_text for token in ("just now", "today", "few moments")):
        return 0
    match = re.search(
        r"(\d+)\s*(min|mins|minute|minutes|hr|hrs|hour|hours|day|days|week|weeks|month|months)",
        posted_text,
    )
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    unit_minutes = {
        "min": 1,
        "mins": 1,
        "minute": 1,
        "minutes": 1,
        "hr": 60,
        "hrs": 60,
        "hour": 60,
        "hours": 60,
        "day": 1440,
        "days": 1440,
        "week": 10080,
        "weeks": 10080,
        "month": 43200,
        "months": 43200,
    }
    return amount * unit_minutes[unit]


def _feature_map(job: dict, profile: dict) -> tuple[dict[str, float], list[str], list[str]]:
    title = _normalize_term(job.get("title", ""))
    description = _normalize_term(job.get("description", ""))
    location = _normalize_term(job.get("location", ""))
    corpus = " ".join(part for part in [title, description, location] if part)

    features: dict[str, float] = {}
    matched_terms: list[str] = []
    signals: list[str] = []

    skills = _unique_terms(profile.get("skills", []) or [])
    keywords = _unique_terms(profile.get("keywords", []) or [])
    role = _normalize_term(profile.get("role", ""))
    preferred_location = _normalize_term(profile.get("location", ""))

    for skill in skills:
        score = 0.0
        if skill in title:
            score += 1.2
        if skill in description:
            score += 1.0
        if score:
            features[f"skill:{skill}"] = score
            matched_terms.append(skill)

    for keyword in keywords:
        score = 0.0
        if keyword in title:
            score += 1.3
        if keyword in description:
            score += 0.8
        if score:
            features[f"keyword:{keyword}"] = score
            matched_terms.append(keyword)

    if role and (role in title or role in description):
        features["profile_role_match"] = 1.0

    if preferred_location and preferred_location in location:
        features["location_match"] = 0.8

    if "remote" in corpus:
        features["remote_signal"] = 0.4
        signals.append("remote")

    if any(term in corpus for term in ("intern", "junior", "entry level", "fresher", "trainee")):
        features["entry_signal"] = 0.8
        signals.append("entry")

    if any(term in corpus for term in ("senior", "lead", "manager", "principal", "director", "staff", "architect")):
        features["seniority_signal"] = 1.0
        signals.append("senior")

    if int(job.get("easy_apply") or 0) == 1:
        features["easy_apply_signal"] = 1.0
        signals.append("easy_apply")

    posted_minutes_ago = _posted_minutes_ago(job)
    if posted_minutes_ago is not None and posted_minutes_ago <= 24 * 60:
        features["fresh_24h_signal"] = 0.9
        signals.append("fresh_24h")
    elif posted_minutes_ago is not None and posted_minutes_ago <= 7 * 24 * 60:
        features["fresh_7d_signal"] = 0.5
        signals.append("fresh_7d")

    return features, list(dict.fromkeys(matched_terms)), list(dict.fromkeys(signals))


def _heuristic_evaluate_job(job: dict, profile: dict) -> dict:
    model_state = {}
    features, matched_terms, signals = _feature_map(job, profile)

    heuristic_score = 42
    heuristic_score += sum(value * 8 for name, value in features.items() if name.startswith("skill:"))
    heuristic_score += sum(value * 9 for name, value in features.items() if name.startswith("keyword:"))
    heuristic_score += 10 if "profile_role_match" in features else 0
    heuristic_score += 4 if "location_match" in features else 0
    heuristic_score += 2 if "remote_signal" in features else 0
    heuristic_score += 5 if "entry_signal" in features else 0
    heuristic_score += 8 if "easy_apply_signal" in features else 0
    heuristic_score += 6 if "fresh_24h_signal" in features else 0
    heuristic_score += 3 if "fresh_7d_signal" in features else 0
    heuristic_score -= 18 if "seniority_signal" in features else 0

    weights = model_state.get("weights", {}) or {}
    bias = float(model_state.get("bias", 0.0) or 0.0)
    learned_adjustment = bias
    for name, value in features.items():
        learned_adjustment += float(weights.get(name, 0.0) or 0.0) * value

    score = round(max(0, min(100, heuristic_score + (learned_adjustment * 10))))
    priority_score = score
    priority_score += 8 if "easy_apply_signal" in features else 0
    priority_score += 4 if "fresh_24h_signal" in features else 0
    priority_score += 2 if "fresh_7d_signal" in features else 0
    confused = abs(score - 70) <= 5
    return {
        "apply": score >= 70,
        "score": score,
        "priority_score": round(priority_score, 2),
        "confused": confused,
        "heuristic_score": round(heuristic_score, 2),
        "learned_adjustment": round(learned_adjustment * 10, 2),
        "matched_terms": matched_terms[:6],
        "signals": signals[:6],
        "trained_examples": int(model_state.get("trained_examples", 0) or 0),
    }


def _build_job_prompt(job: dict, profile: dict) -> str:
    skills = ", ".join(profile.get("skills", []) or ["security"])
    keywords = ", ".join(profile.get("keywords", []) or ["security"])
    role = profile.get("role", "cybersecurity")
    location = profile.get("location", "")

    job_info = f"""
Job Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}
Easy Apply: {'Yes' if job.get('easy_apply') else 'No'}
Posted: {job.get('posted_text', job.get('posted_at', 'N/A'))}
"""
    if job.get("description"):
        job_info += f"\nDescription:\n{job.get('description', '')[:2000]}"

    profile_info = f"""
Candidate Profile:
- Role: {role}
- Skills: {skills}
- Target Keywords: {keywords}
- Preferred Location: {location}
"""

    return f"""You are a job matching assistant. Evaluate if this job is a good match for the candidate.

{job_info}
{profile_info}

Respond with EXACTLY one line in this format:
SCORE: <0-100> | DECISION: <APPLY|REJECT|REVIEW> | REASON: <brief reason>

Scoring guidelines:
- 80-100: Strong match - skills align, good fit
- 60-79: Good match - reasonable fit
- 40-59: Weak match - partial alignment
- 0-39: Poor match - not suitable

REVIEW if you need more information or are uncertain.
REJECT if the job requires senior experience the candidate doesn't have, or is completely unrelated."""


def evaluate_job(
    job: dict,
    profile: dict,
    min_score: int = 70,
    uncertainty_margin: int = 5,
    model_state: dict | None = None,
) -> dict:
    """Evaluate if a job matches the candidate profile."""
    return _heuristic_evaluate_job(job, profile)


def update_model(
    job: dict,
    profile: dict,
    label: str,
    model_state: dict | None = None,
) -> dict:
    model_state = model_state or {}
    normalized_label = _normalize_term(label)
    if normalized_label in POSITIVE_LABELS:
        target = 1
    elif normalized_label in NEGATIVE_LABELS:
        target = -1
    else:
        return {
            "weights": dict(model_state.get("weights", {}) or {}),
            "bias": float(model_state.get("bias", 0.0) or 0.0),
            "trained_examples": int(model_state.get("trained_examples", 0) or 0),
        }

    features, matched_terms, _signals = _feature_map(job, profile)
    weights = dict(model_state.get("weights", {}) or {})
    bias = float(model_state.get("bias", 0.0) or 0.0)
    trained_examples = int(model_state.get("trained_examples", 0) or 0)

    learning_rate = 0.35
    bias_step = 0.2
    for name, value in features.items():
        weights[name] = round(float(weights.get(name, 0.0) or 0.0) + (target * learning_rate * value), 6)
    bias = round(bias + (target * bias_step), 6)

    return {
        "weights": weights,
        "bias": bias,
        "trained_examples": trained_examples + 1,
        "updated_features": matched_terms[:6],
    }
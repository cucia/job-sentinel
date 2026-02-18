def _score_from_text(text: str, keywords: list[str]) -> int:
    if not text:
        return 0
    text_l = text.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in text_l:
            score += 10
    return score


def evaluate_job(job: dict, profile: dict, min_score: int, uncertainty_margin: int) -> dict:
    description = (job.get("description") or "")
    title = (job.get("title") or "")

    skills = profile.get("skills", []) or []
    keywords = profile.get("keywords", []) or []

    score = 50
    score += _score_from_text(description, skills)
    score += _score_from_text(title, keywords)

    confused = abs(score - min_score) <= uncertainty_margin
    return {
        "apply": score >= min_score,
        "score": score,
        "confused": confused,
    }


def update_model(*_args, **_kwargs) -> dict:
    return {}

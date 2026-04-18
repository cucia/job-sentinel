def policy_allows(job: dict, policy: dict) -> bool:
    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()

    blocked_keywords = [k.lower() for k in policy.get("blocked_keywords", [])]
    for keyword in blocked_keywords:
        if keyword in title or keyword in description:
            return False

    allowed_roles = [k.lower() for k in policy.get("allowed_roles", [])]
    if allowed_roles:
        if not any(role in title or role in description for role in allowed_roles):
            return False

    required_skills = [k.lower() for k in policy.get("required_skills", [])]
    if required_skills:
        if not any(skill in description for skill in required_skills):
            return False

    return True

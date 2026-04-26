"""
Enhanced Pre-Apply Scoring with Quality Metrics

Evaluates job fit quality before application to maximize shortlist probability.
"""

import re
from typing import Dict, List, Tuple


def evaluate_fit(profile: dict, job: dict) -> dict:
    """
    Comprehensive job fit evaluation with quality metrics.

    Args:
        profile: Candidate profile
        job: Job details

    Returns:
        {
            "overall_score": 0-100,
            "skill_match_percent": 0-100,
            "experience_match": 0-100,
            "role_alignment": 0-100,
            "keyword_overlap": 0-100,
            "quality_tier": "high" | "medium" | "low",
            "should_apply": bool,
            "reasons": [str]
        }
    """
    # Extract job and profile data
    title = _normalize(job.get("title", ""))
    description = _normalize(job.get("description", ""))
    job_text = f"{title} {description}"

    profile_skills = [_normalize(s) for s in profile.get("skills", [])]
    profile_keywords = [_normalize(k) for k in profile.get("keywords", [])]
    profile_role = _normalize(profile.get("role", ""))
    profile_experience = profile.get("experience", "")

    # Calculate individual metrics
    skill_match = _calculate_skill_match(profile_skills, job_text)
    experience_match = _calculate_experience_match(profile_experience, job_text)
    role_alignment = _calculate_role_alignment(profile_role, profile_keywords, title, description)
    keyword_overlap = _calculate_keyword_overlap(profile_keywords, job_text)

    # Calculate overall score (weighted average)
    overall_score = (
        skill_match * 0.35 +
        experience_match * 0.25 +
        role_alignment * 0.30 +
        keyword_overlap * 0.10
    )

    # Determine quality tier
    quality_tier = _determine_quality_tier(overall_score, skill_match, role_alignment)

    # Decide if should apply
    should_apply = _should_apply_decision(overall_score, quality_tier, skill_match, role_alignment)

    # Generate reasons
    reasons = _generate_reasons(skill_match, experience_match, role_alignment, keyword_overlap, quality_tier)

    return {
        "overall_score": round(overall_score, 2),
        "skill_match_percent": round(skill_match, 2),
        "experience_match": round(experience_match, 2),
        "role_alignment": round(role_alignment, 2),
        "keyword_overlap": round(keyword_overlap, 2),
        "quality_tier": quality_tier,
        "should_apply": should_apply,
        "reasons": reasons,
    }


def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _calculate_skill_match(profile_skills: List[str], job_text: str) -> float:
    """
    Calculate skill match percentage.

    Returns: 0-100 score
    """
    if not profile_skills:
        return 0.0

    matched_skills = 0
    total_skills = len(profile_skills)

    for skill in profile_skills:
        if skill in job_text:
            matched_skills += 1

    match_percent = (matched_skills / total_skills) * 100
    return min(100.0, match_percent)


def _calculate_experience_match(profile_experience: str, job_text: str) -> float:
    """
    Calculate experience level match.

    Returns: 0-100 score
    """
    experience_lower = profile_experience.lower()

    # Extract years from profile
    profile_years = _extract_years(experience_lower)

    # Extract required years from job
    job_years = _extract_required_years(job_text)

    # Check seniority signals
    is_entry_level = any(term in experience_lower for term in ["entry", "junior", "fresher", "0 year", "1 year"])
    job_is_senior = any(term in job_text for term in ["senior", "lead", "manager", "principal", "director", "staff"])
    job_is_entry = any(term in job_text for term in ["entry", "junior", "fresher", "trainee"])

    # Scoring logic
    if is_entry_level and job_is_senior:
        return 20.0  # Mismatch
    elif is_entry_level and job_is_entry:
        return 95.0  # Perfect match
    elif profile_years and job_years:
        if profile_years >= job_years:
            return 90.0  # Meets requirements
        elif profile_years >= job_years * 0.7:
            return 70.0  # Close enough
        else:
            return 40.0  # Under-qualified
    else:
        return 60.0  # Uncertain, neutral score


def _extract_years(text: str) -> int:
    """Extract years of experience from text."""
    match = re.search(r"(\d+)\s*(?:year|yr)", text)
    return int(match.group(1)) if match else 0


def _extract_required_years(text: str) -> int:
    """Extract required years from job description."""
    patterns = [
        r"(\d+)\+?\s*(?:year|yr)s?\s+(?:of\s+)?experience",
        r"minimum\s+(\d+)\s+(?:year|yr)",
        r"at least\s+(\d+)\s+(?:year|yr)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return 0


def _calculate_role_alignment(profile_role: str, profile_keywords: List[str], title: str, description: str) -> float:
    """
    Calculate role alignment score.

    Returns: 0-100 score
    """
    score = 0.0

    # Check if profile role appears in title (highest weight)
    if profile_role and profile_role in title:
        score += 50.0

    # Check if profile role appears in description
    if profile_role and profile_role in description:
        score += 20.0

    # Check keyword matches in title
    keyword_in_title = sum(1 for kw in profile_keywords if kw in title)
    if keyword_in_title > 0:
        score += min(30.0, keyword_in_title * 15.0)

    return min(100.0, score)


def _calculate_keyword_overlap(profile_keywords: List[str], job_text: str) -> float:
    """
    Calculate keyword overlap percentage.

    Returns: 0-100 score
    """
    if not profile_keywords:
        return 0.0

    matched = sum(1 for kw in profile_keywords if kw in job_text)
    overlap_percent = (matched / len(profile_keywords)) * 100
    return min(100.0, overlap_percent)


def _determine_quality_tier(overall_score: float, skill_match: float, role_alignment: float) -> str:
    """
    Determine quality tier based on scores.

    Returns: "high", "medium", or "low"
    """
    # High quality: strong overall score AND good skill/role match
    if overall_score >= 75 and skill_match >= 60 and role_alignment >= 70:
        return "high"
    # Medium quality: decent scores
    elif overall_score >= 55 and (skill_match >= 40 or role_alignment >= 50):
        return "medium"
    # Low quality: weak scores
    else:
        return "low"


def _should_apply_decision(overall_score: float, quality_tier: str, skill_match: float, role_alignment: float) -> bool:
    """
    Decide if should apply based on quality metrics.

    Returns: True if should apply
    """
    # Only apply to high and medium quality jobs
    if quality_tier == "high":
        return True
    elif quality_tier == "medium":
        # For medium tier, require minimum thresholds
        return overall_score >= 60 and (skill_match >= 40 or role_alignment >= 50)
    else:
        # Skip low quality jobs
        return False


def _generate_reasons(skill_match: float, experience_match: float, role_alignment: float, keyword_overlap: float, quality_tier: str) -> List[str]:
    """Generate human-readable reasons for the decision."""
    reasons = []

    if quality_tier == "high":
        reasons.append("High quality match")
    elif quality_tier == "low":
        reasons.append("Low quality match - skip to improve success rate")

    if skill_match >= 70:
        reasons.append(f"Strong skill match ({skill_match:.0f}%)")
    elif skill_match < 30:
        reasons.append(f"Weak skill match ({skill_match:.0f}%)")

    if role_alignment >= 70:
        reasons.append("Role aligns well with profile")
    elif role_alignment < 40:
        reasons.append("Role misalignment")

    if experience_match >= 80:
        reasons.append("Experience level matches")
    elif experience_match < 50:
        reasons.append("Experience mismatch")

    return reasons[:4]  # Limit to 4 reasons

import os
import yaml


def _profiles_dir(base_dir: str) -> str:
    return os.path.join(base_dir, "profiles")


def _profile_path(base_dir: str, name: str) -> str:
    safe = name.strip().lower().replace(" ", "_")
    return os.path.join(_profiles_dir(base_dir), f"{safe}.yaml")


def load_profile(base_dir: str, name: str) -> dict:
    path = _profile_path(base_dir, name)
    if not os.path.exists(path):
        return {"name": name}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"name": name}


def save_profile(base_dir: str, name: str, profile: dict) -> None:
    os.makedirs(_profiles_dir(base_dir), exist_ok=True)
    path = _profile_path(base_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(profile, f, sort_keys=False)


def init_profile_from_resume(base_dir: str, resume_data: dict) -> dict:
    """
    Initialize a profile from parsed resume data.

    Args:
        base_dir: Base directory for profiles
        resume_data: Dictionary from resume_parser.parse_resume()

    Returns:
        Profile dictionary ready for user verification
    """
    profile = {
        "name": resume_data.get("name", ""),
        "email": resume_data.get("email", ""),
        "phone": resume_data.get("phone", ""),
        "skills": resume_data.get("skills", []),
        "experience": resume_data.get("experience", ""),
        "education": resume_data.get("education", ""),
        "linkedin_url": resume_data.get("linkedin_url", ""),
        "github_url": resume_data.get("github_url", ""),
        "portfolio_url": resume_data.get("portfolio_url", ""),
        "current_company": resume_data.get("current_company", ""),
        "role": resume_data.get("role", ""),
    }
    return {k: v for k, v in profile.items() if v}


def update_profile_fields(base_dir: str, name: str, updates: dict) -> dict:
    """
    Update specific fields in an existing profile.

    Args:
        base_dir: Base directory for profiles
        name: Profile name
        updates: Dictionary of fields to update

    Returns:
        Updated profile dictionary
    """
    profile = load_profile(base_dir, name)
    profile.update(updates)
    save_profile(base_dir, name, profile)
    return profile


def get_missing_fields(profile: dict) -> list[str]:
    """
    Identify missing critical fields in a profile.

    Args:
        profile: Profile dictionary

    Returns:
        List of missing field names
    """
    required_fields = {
        "name": "Full Name",
        "email": "Email Address",
        "phone": "Phone Number",
        "role": "Preferred Job Role",
        "location": "Preferred Location",
        "experience": "Years of Experience",
    }

    missing = []
    for field, label in required_fields.items():
        if not profile.get(field):
            missing.append(label)

    return missing

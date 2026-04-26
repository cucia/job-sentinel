"""
CLI Onboarding Module for Job Sentinel

Handles resume-based profile creation with user verification.
"""

import os
import sys
from typing import Optional


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def _print_field(label: str, value: any) -> None:
    if isinstance(value, list):
        value_str = ", ".join(str(v) for v in value) if value else "(not found)"
    else:
        value_str = str(value) if value else "(not found)"
    print(f"  {label:20s}: {value_str}")


def _prompt_input(label: str, current_value: any = None) -> str:
    if current_value:
        prompt = f"{label} [{current_value}]: "
    else:
        prompt = f"{label}: "
    return input(prompt).strip()


def _confirm(message: str) -> bool:
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print("Please enter 'y' or 'n'")


def display_extracted_data(profile: dict) -> None:
    """Display extracted profile data to user."""
    _print_section("Extracted Profile Data")
    _print_field("Name", profile.get("name"))
    _print_field("Email", profile.get("email"))
    _print_field("Phone", profile.get("phone"))
    _print_field("Skills", profile.get("skills"))
    _print_field("Experience", profile.get("experience"))
    _print_field("Education", profile.get("education"))
    _print_field("Current Company", profile.get("current_company"))
    _print_field("Current Role", profile.get("role"))
    _print_field("LinkedIn", profile.get("linkedin_url"))
    _print_field("GitHub", profile.get("github_url"))
    print()


def verify_and_edit_profile(profile: dict) -> dict:
    """Allow user to verify and edit extracted data."""
    _print_section("Profile Verification")
    print("Review the extracted data. Press Enter to keep current value, or type new value.")
    print()

    fields = [
        ("name", "Full Name"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("role", "Preferred Job Role"),
        ("location", "Preferred Location"),
        ("experience", "Years of Experience"),
        ("current_company", "Current Company"),
        ("education", "Education"),
        ("linkedin_url", "LinkedIn URL"),
        ("github_url", "GitHub URL"),
        ("portfolio_url", "Portfolio URL"),
    ]

    updated = profile.copy()

    for field_key, field_label in fields:
        current = updated.get(field_key)
        new_value = _prompt_input(field_label, current)
        if new_value:
            updated[field_key] = new_value
        elif not current:
            updated[field_key] = ""

    if "skills" in profile:
        print(f"\nCurrent Skills: {', '.join(profile['skills'])}")
        skills_input = input("Update skills (comma-separated, or press Enter to keep): ").strip()
        if skills_input:
            updated["skills"] = [s.strip() for s in skills_input.split(",") if s.strip()]

    return updated


def prompt_missing_fields(profile: dict) -> dict:
    """Prompt user for missing critical fields."""
    from src.ai.profile_store import get_missing_fields

    missing = get_missing_fields(profile)
    if not missing:
        return profile

    _print_section("Missing Information")
    print("Please provide the following required information:")
    print()

    field_map = {
        "Full Name": "name",
        "Email Address": "email",
        "Phone Number": "phone",
        "Preferred Job Role": "role",
        "Preferred Location": "location",
        "Years of Experience": "experience",
    }

    updated = profile.copy()
    for label in missing:
        field_key = field_map.get(label)
        if field_key:
            value = input(f"{label}: ").strip()
            if value:
                updated[field_key] = value

    return updated


def onboard_from_resume(resume_path: str, profile_name: Optional[str] = None) -> None:
    """
    Main onboarding flow: parse resume, verify data, save profile.

    Args:
        resume_path: Path to resume file
        profile_name: Optional profile name (defaults to extracted name)
    """
    from src.ai.resume_parser import parse_resume
    from src.ai.profile_store import init_profile_from_resume, save_profile

    base_dir = _base_dir()

    print("\n" + "=" * 60)
    print("  Job Sentinel - Resume Onboarding")
    print("=" * 60)
    print(f"\nParsing resume: {resume_path}")

    try:
        resume_data = parse_resume(resume_path, use_llm=True)
    except Exception as e:
        print(f"\nError parsing resume: {e}")
        sys.exit(1)

    profile = init_profile_from_resume(base_dir, resume_data)

    if not profile.get("name"):
        print("\nCould not extract name from resume.")
        name = input("Please enter your full name: ").strip()
        if not name:
            print("Name is required. Exiting.")
            sys.exit(1)
        profile["name"] = name

    display_extracted_data(profile)

    if not _confirm("Does this look correct?"):
        profile = verify_and_edit_profile(profile)

    profile = prompt_missing_fields(profile)

    name_for_profile = profile_name or profile.get("name", "default")

    _print_section("Saving Profile")
    print(f"Profile name: {name_for_profile}")

    try:
        save_profile(base_dir, name_for_profile, profile)
        print(f"\n✓ Profile saved successfully!")
        print(f"  Location: profiles/{name_for_profile.lower().replace(' ', '_')}.yaml")
        print("\nYou can now run Job Sentinel with this profile.")
    except Exception as e:
        print(f"\nError saving profile: {e}")
        sys.exit(1)


def main() -> None:
    """CLI entry point for onboarding."""
    import argparse

    parser = argparse.ArgumentParser(description="Job Sentinel Onboarding")
    parser.add_argument("--resume", required=True, help="Path to resume file (PDF, DOCX, or TXT)")
    parser.add_argument("--name", help="Profile name (defaults to extracted name)")

    args = parser.parse_args()

    if not os.path.exists(args.resume):
        print(f"Error: Resume file not found: {args.resume}")
        sys.exit(1)

    onboard_from_resume(args.resume, args.name)


if __name__ == "__main__":
    main()

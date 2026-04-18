import os
import yaml


def _load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _profiles_dir(base_dir: str) -> str:
    return os.path.join(base_dir, "profiles")


def _profile_path(base_dir: str, name: str) -> str:
    safe = name.strip().lower().replace(" ", "_")
    return os.path.join(_profiles_dir(base_dir), f"{safe}.yaml")


def default_profile_name(base_dir: str) -> str:
    profiles_dir = _profiles_dir(base_dir)
    if os.path.isdir(profiles_dir):
        names = sorted(
            os.path.splitext(name)[0]
            for name in os.listdir(profiles_dir)
            if name.endswith(".yaml")
        )
        if names:
            return names[0]
    return "candidate"


def load_settings(base_dir: str) -> dict:
    return _load_yaml(os.path.join(base_dir, "configs", "settings.yaml"))


def load_profile(base_dir: str, profile_name: str | None = None) -> dict:
    profile = _load_yaml(os.path.join(base_dir, "configs", "profile.yaml"))
    chosen_profile = profile_name or default_profile_name(base_dir)
    profile_override = _load_yaml(_profile_path(base_dir, chosen_profile))
    if profile_override:
        profile.update(profile_override)
    profile.setdefault("name", profile_override.get("name") if profile_override else chosen_profile)
    return profile


def save_settings(base_dir: str, settings: dict) -> None:
    path = os.path.join(base_dir, "configs", "settings.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, sort_keys=False)

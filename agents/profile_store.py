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

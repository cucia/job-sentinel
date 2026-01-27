import os
import yaml


def _load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings(base_dir: str) -> dict:
    return _load_yaml(os.path.join(base_dir, "configs", "settings.yaml"))


def load_profile(base_dir: str) -> dict:
    return _load_yaml(os.path.join(base_dir, "configs", "profile.yaml"))


def save_settings(base_dir: str, settings: dict) -> None:
    path = os.path.join(base_dir, "configs", "settings.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, sort_keys=False)

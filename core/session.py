import os
import sys

from core.browser import open_context, close_context, save_storage_state
from core.config import load_settings
from core.logger import log


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_session_path(base_dir: str, settings: dict, platform: str) -> str:
    sessions = settings.get("platforms", {}).get("sessions", {})
    path = sessions.get(platform, f"sessions/{platform}.json")
    if os.path.isabs(path):
        return path
    return os.path.join(base_dir, path)


def ensure_session(settings: dict, platform: str, login_url: str) -> str:
    base_dir = _base_dir()
    session_path = get_session_path(base_dir, settings, platform)
    if os.path.exists(session_path):
        return session_path

    log(f"No session found for {platform}. Opening login page...")

    playwright, browser, context = open_context(headless=False)
    try:
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded")
        input("Login in the opened browser, then press Enter here to continue...")
        save_storage_state(context, session_path)
        log(f"Session saved to {session_path}")
    finally:
        close_context(playwright, browser, context)

    return session_path


def main() -> None:
    if len(sys.argv) < 3:
        log("Usage: python core/session.py <platform> <login_url>")
        sys.exit(1)

    platform = sys.argv[1].strip()
    login_url = sys.argv[2].strip()

    settings = load_settings(_base_dir())
    ensure_session(settings, platform, login_url)


if __name__ == "__main__":
    main()

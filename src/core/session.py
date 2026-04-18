import os
import sys

from .async_runner import run
from .browser import open_context, close_context, save_storage_state
from .config import load_settings
from .logger import log


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_session_path(base_dir: str, settings: dict, platform: str) -> str:
    sessions = settings.get("platforms", {}).get("sessions", {})
    path = sessions.get(platform, f"sessions/{platform}.json")
    if os.path.isabs(path):
        return path
    return os.path.join(base_dir, path)


def _can_prompt_for_login() -> bool:
    try:
        return bool(sys.stdin and sys.stdin.isatty())
    except Exception:
        return False


def ensure_session(settings: dict, platform: str, login_url: str) -> str:
    base_dir = _base_dir()
    session_path = get_session_path(base_dir, settings, platform)
    log(f"Session base_dir={base_dir}")
    log(f"Session path={session_path}")
    if os.path.exists(session_path):
        log("Session file already exists")
        return session_path

    has_display = bool(os.environ.get("DISPLAY")) or os.name == "nt"
    if not has_display:
        log(
            f"No session for {platform}. No GUI display is available here. "
            "Save the session from the dashboard or run the session script on the host."
        )
        return ""

    if not _can_prompt_for_login():
        log(
            f"No session for {platform}. This process is non-interactive, so login cannot be completed here. "
            "Save the session from the dashboard first."
        )
        return ""

    log(f"No session found for {platform}. Opening login page...")

    async def _login():
        playwright, browser, context = await open_context(headless=False)
        try:
            page = await context.new_page()
            log(f"Opening URL: {login_url}")
            await page.goto(login_url, wait_until="domcontentloaded")
            input("Login in the opened browser, then press Enter here to continue...")
            await save_storage_state(context, session_path)
            log(f"Session saved to {session_path}")
        finally:
            await close_context(playwright, browser, context)

    run(_login())

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

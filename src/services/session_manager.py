import os
import queue
import threading
from datetime import datetime

from src.core.session import get_session_path


LOGIN_URLS = {
    "linkedin": "https://www.linkedin.com/login",
    "indeed": "https://www.indeed.com/account/login",
    "naukri": "https://www.naukri.com/nlogin/login",
}
LOGIN_CHECK_URLS = {
    "linkedin": "https://www.linkedin.com/feed/",
}

_STATE_LOCK = threading.RLock()
_PENDING_LOGINS: dict[str, dict] = {}
_STATUS_CACHE: dict[str, dict] = {}

try:
    from playwright.sync_api import sync_playwright
except Exception as exc:  # pragma: no cover - import guard for local environments
    sync_playwright = None
    _PLAYWRIGHT_IMPORT_ERROR = str(exc)
else:
    _PLAYWRIGHT_IMPORT_ERROR = ""


def _debug_artifact_path(base_dir: str, filename: str) -> str:
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, filename)


def _set_status(platform: str, session_path: str, status: str, detail: str) -> None:
    with _STATE_LOCK:
        _STATUS_CACHE[platform] = {
            "session_path": session_path,
            "status": status,
            "detail": detail,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
        }


def _clear_status(platform: str) -> None:
    with _STATE_LOCK:
        _STATUS_CACHE.pop(platform, None)


def _cached_status(platform: str, session_path: str) -> dict | None:
    with _STATE_LOCK:
        status = _STATUS_CACHE.get(platform)
        if not status:
            return None
        if status.get("session_path") != session_path:
            return None
        return dict(status)


def interactive_login_supported() -> tuple[bool, str]:
    if sync_playwright is None:
        return False, f"Playwright is not available in this dashboard environment: {_PLAYWRIGHT_IMPORT_ERROR}"
    if os.name == "nt":
        return True, ""
    if os.environ.get("DISPLAY"):
        return True, ""
    if os.path.exists("/.dockerenv"):
        return False, "Interactive login needs the dashboard on the host machine or a GUI-enabled container."
    return False, "Interactive login needs a GUI display."


def _drop_pending_login(platform: str, state: dict | None = None) -> None:
    current = _PENDING_LOGINS.get(platform)
    if current is None:
        return
    if state is not None and current is not state:
        return
    _PENDING_LOGINS.pop(platform, None)


def _interactive_login_worker(platform: str, session_path: str, state: dict) -> None:
    playwright = None
    browser = None
    context = None
    try:
        playwright = sync_playwright().start()
        # Use Firefox for better stealth (configurable)
        browser_type = settings.get("app", {}).get("browser", "firefox") if settings else "firefox"

        if browser_type == "firefox":
            browser = playwright.firefox.launch(
                headless=False,
                firefox_user_prefs={
                    'dom.webdriver.enabled': False,
                    'useAutomationExtension': False,
                }
            )
        elif browser_type == "webkit":
            browser = playwright.webkit.launch(headless=False)
        else:  # chromium fallback
            browser = playwright.chromium.launch(headless=False)

        if os.path.exists(session_path):
            context = browser.new_context(storage_state=session_path)
        else:
            context = browser.new_context()
        page = context.new_page()
        page.goto(LOGIN_URLS[platform], wait_until="domcontentloaded")
        state["startup"].put((True, ""))

        while True:
            command = state["commands"].get()
            action = command["action"]
            reply = command["reply"]
            if action == "save":
                try:
                    context.storage_state(path=session_path)
                    _set_status(platform, session_path, "saved", "Session file saved from the interactive login flow.")
                    reply.put((True, f"{platform.capitalize()} session saved to {session_path}."))
                except Exception as exc:
                    _set_status(platform, session_path, "error", f"Could not save the session: {exc}")
                    reply.put((False, f"Could not save the {platform} session: {exc}"))
                break
            if action == "cancel":
                if os.path.exists(session_path):
                    _set_status(platform, session_path, "saved", "Saved session file found.")
                else:
                    _clear_status(platform)
                reply.put((True, f"{platform.capitalize()} login flow cancelled."))
                break
            reply.put((False, f"Unsupported login command: {action}"))
    except Exception as exc:
        try:
            state["startup"].put((False, f"Could not open the login browser for {platform}: {exc}"))
        except Exception:
            pass
    finally:
        try:
            if context:
                context.close()
        except Exception:
            pass
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            if playwright:
                playwright.stop()
        except Exception:
            pass
        with _STATE_LOCK:
            _drop_pending_login(platform, state)


def _send_pending_command(platform: str, action: str, timeout_seconds: int = 30) -> tuple[bool, str]:
    with _STATE_LOCK:
        state = _PENDING_LOGINS.get(platform)
        if not state:
            return False, f"No active login flow for {platform}."
        reply: queue.Queue = queue.Queue(maxsize=1)
        state["commands"].put({"action": action, "reply": reply})
    try:
        ok, message = reply.get(timeout=timeout_seconds)
        return bool(ok), str(message)
    except queue.Empty:
        return False, f"Timed out while waiting for the {platform} login flow."


def _linkedin_authenticated_page(page) -> tuple[bool, str]:
    current_url = (page.url or "").lower()
    if any(token in current_url for token in ("checkpoint", "challenge")):
        return False, "LinkedIn asked for extra verification before the session could be saved."
    if any(token in current_url for token in ("login", "authwall")):
        return False, "LinkedIn redirected back to the login page."
    if page.query_selector("input#username, input[name='session_key'], form.login__form"):
        return False, "LinkedIn login form is still visible."
    if page.query_selector("nav[aria-label='Primary Navigation'], div.global-nav, input[placeholder*='Search']"):
        return True, "LinkedIn session looks authenticated."
    return True, f"LinkedIn opened {page.url} without showing the login form."


def _save_debug_artifacts(base_dir: str, page, prefix: str) -> None:
    try:
        page.screenshot(
            path=_debug_artifact_path(base_dir, f"{prefix}.png"),
            full_page=True,
        )
    except Exception:
        pass
    try:
        with open(_debug_artifact_path(base_dir, f"{prefix}.html"), "w", encoding="utf-8") as f:
            f.write(page.content())
    except Exception:
        pass


def session_overview(base_dir: str, settings: dict) -> dict:
    supported, reason = interactive_login_supported()
    with _STATE_LOCK:
        pending = set(_PENDING_LOGINS.keys())

    info = {}
    for platform in LOGIN_URLS:
        path = get_session_path(base_dir, settings, platform)
        exists = os.path.exists(path)
        cached = _cached_status(platform, path)
        if platform in pending:
            login_status = "pending"
            login_detail = "Login browser is open. Finish sign-in and click Save session."
            checked_at = cached.get("checked_at") if cached else None
        elif cached:
            login_status = cached.get("status", "saved")
            login_detail = cached.get("detail", "")
            checked_at = cached.get("checked_at")
        elif exists:
            login_status = "saved"
            login_detail = "Saved session file found."
            checked_at = None
        else:
            login_status = "missing"
            login_detail = "No saved session file found."
            checked_at = None
        info[platform] = {
            "path": path,
            "exists": exists,
            "size": os.path.getsize(path) if exists else 0,
            "updated_at": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds") if exists else None,
            "pending": platform in pending,
            "login_status": login_status,
            "login_detail": login_detail,
            "checked_at": checked_at,
        }

    return {
        "supported": supported,
        "reason": reason,
        "platforms": info,
    }


def start_session_login(base_dir: str, settings: dict, platform: str) -> tuple[bool, str]:
    if platform not in LOGIN_URLS:
        return False, f"Unsupported platform: {platform}"

    supported, reason = interactive_login_supported()
    if not supported:
        return False, reason

    with _STATE_LOCK:
        if platform in _PENDING_LOGINS:
            return True, f"{platform.capitalize()} login is already open. Finish login, then click Save session."

        session_path = get_session_path(base_dir, settings, platform)
        os.makedirs(os.path.dirname(session_path), exist_ok=True)
        state = {
            "session_path": session_path,
            "commands": queue.Queue(),
            "startup": queue.Queue(maxsize=1),
        }
        thread = threading.Thread(
            target=_interactive_login_worker,
            args=(platform, session_path, state),
            daemon=True,
            name=f"jobsentinel-login-{platform}",
        )
        state["thread"] = thread
        _PENDING_LOGINS[platform] = state
        _set_status(platform, session_path, "pending", "Login browser is open.")
        thread.start()

    try:
        ok, startup_message = state["startup"].get(timeout=20)
    except queue.Empty:
        return True, (
            f"{platform.capitalize()} login is starting. "
            "Open the browser view, finish sign-in, then click Save session."
        )
    if not ok:
        _set_status(platform, session_path, "error", startup_message)
        return False, startup_message
    return True, (
        f"{platform.capitalize()} login opened in a browser window. "
        "Sign in there, then return here and click Save session."
    )


def save_session_login(platform: str) -> tuple[bool, str]:
    return _send_pending_command(platform, "save")


def cancel_session_login(platform: str) -> tuple[bool, str]:
    return _send_pending_command(platform, "cancel")


def delete_session_file(base_dir: str, settings: dict, platform: str) -> tuple[bool, str]:
    if platform not in LOGIN_URLS:
        return False, f"Unsupported platform: {platform}"

    with _STATE_LOCK:
        pending = platform in _PENDING_LOGINS
    if pending:
        cancel_session_login(platform)

    session_path = get_session_path(base_dir, settings, platform)
    if not os.path.exists(session_path):
        _set_status(platform, session_path, "missing", "No saved session file found.")
        return False, f"No saved session file found for {platform}."

    os.remove(session_path)
    _set_status(platform, session_path, "missing", "Saved session file deleted.")
    return True, f"Deleted saved session file for {platform}."


def validate_saved_session(base_dir: str, settings: dict, platform: str) -> tuple[bool, str]:
    if platform not in LOGIN_URLS:
        return False, f"Unsupported platform: {platform}"

    session_path = get_session_path(base_dir, settings, platform)
    if not os.path.exists(session_path):
        _set_status(platform, session_path, "missing", "No saved session file found.")
        return False, f"No saved session file found for {platform}."

    if platform != "linkedin":
        _set_status(platform, session_path, "saved", f"{platform.capitalize()} session file is present.")
        return True, f"{platform.capitalize()} session file is present."

    supported, reason = interactive_login_supported()
    if sync_playwright is None:
        _set_status(platform, session_path, "error", reason)
        return False, reason

    browser = None
    context = None
    playwright = None
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()
        page.goto(LOGIN_CHECK_URLS[platform], wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        ok, detail = _linkedin_authenticated_page(page)
        if not ok:
            _save_debug_artifacts(base_dir, page, "linkedin_session_check")
        _set_status(platform, session_path, "ready" if ok else "expired", detail)
        return ok, detail
    except Exception as exc:
        detail = f"Could not verify the LinkedIn session: {exc}"
        _set_status(platform, session_path, "error", detail)
        return False, detail
    finally:
        try:
            if context:
                context.close()
        except Exception:
            pass
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            if playwright:
                playwright.stop()
        except Exception:
            pass


def login_linkedin_with_credentials(base_dir: str, settings: dict, email: str, password: str) -> tuple[bool, str]:
    email = (email or "").strip()
    password = (password or "").strip()
    if not email or not password:
        return False, "Enter both LinkedIn email and password."
    if sync_playwright is None:
        return False, f"Playwright is not available in this dashboard environment: {_PLAYWRIGHT_IMPORT_ERROR}"

    session_path = get_session_path(base_dir, settings, "linkedin")
    os.makedirs(os.path.dirname(session_path), exist_ok=True)

    browser = None
    context = None
    playwright = None
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(LOGIN_URLS["linkedin"], wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)
        page.fill("input#username, input[name='session_key']", email)
        page.fill("input#password, input[name='session_password']", password)
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)

        ok, detail = _linkedin_authenticated_page(page)
        if not ok:
            _save_debug_artifacts(base_dir, page, "linkedin_login_error")
            status = "challenge" if "verification" in detail.lower() else "expired"
            _set_status("linkedin", session_path, status, detail)
            return False, detail

        context.storage_state(path=session_path)
        _set_status("linkedin", session_path, "ready", "LinkedIn session saved and authenticated.")
        return True, f"LinkedIn session saved to {session_path}."
    except Exception as exc:
        detail = f"Could not complete the LinkedIn login flow: {exc}"
        _set_status("linkedin", session_path, "error", detail)
        return False, detail
    finally:
        try:
            if context:
                context.close()
        except Exception:
            pass
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            if playwright:
                playwright.stop()
        except Exception:
            pass

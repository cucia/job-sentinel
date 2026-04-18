import os

from src.ai.form_filler import fill_application_form
from src.core.config import load_profile
from src.core.async_runner import run
from src.core.browser import close_context, open_context
from src.core.logger import log
from src.core.session import ensure_session, get_session_path
from src.platforms.linkedin.url_utils import normalize_job_url


EASY_APPLY_SELECTORS = [
    "button.jobs-apply-button",
    "button[aria-label*='Easy Apply']",
    "button:has-text('Easy Apply')",
]
SUBMIT_SELECTORS = [
    "button[aria-label='Submit application']",
    "button[aria-label*='Submit application']",
    "button:has-text('Submit application')",
    "button:has-text('Send application')",
]
NEXT_SELECTORS = [
    "button[aria-label='Continue to next step']",
    "button[aria-label*='Continue to next step']",
    "button[aria-label='Review your application']",
    "button[aria-label*='Review your application']",
    "button[aria-label='Next']",
    "button:has-text('Next')",
    "button:has-text('Review')",
]
SUCCESS_SELECTORS = [
    "div.jobs-easy-apply-content__success",
    "h3:has-text('Application submitted')",
    "h2:has-text('Application submitted')",
    "div[role='alert']:has-text('application was sent')",
    "span:has-text('Applied')",
]
DONE_SELECTORS = [
    "button[aria-label='Done']",
    "button[aria-label*='Done']",
    "button:has-text('Done')",
]
MODAL_SELECTORS = [
    "div.jobs-easy-apply-modal",
    "div[role='dialog']",
]
ERROR_SELECTORS = [
    "div[role='alert']",
    ".artdeco-inline-feedback--error",
    ".artdeco-inline-feedback__message",
]
LOGIN_GUARDS = ["login", "checkpoint", "challenge", "authwall"]


def _debug_artifact_path(base_dir: str, filename: str) -> str:
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, filename)


async def _first_visible_locator(page, selectors: list[str]):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() == 0:
                continue
            if await locator.is_visible():
                return locator
        except Exception:
            continue
    return None


async def _click_first(page, selectors: list[str]) -> bool:
    locator = await _first_visible_locator(page, selectors)
    if not locator:
        return False
    try:
        await locator.scroll_into_view_if_needed()
    except Exception:
        pass
    try:
        if hasattr(locator, "is_enabled") and not await locator.is_enabled():
            return False
    except Exception:
        pass
    await locator.click()
    return True


async def _has_visible(page, selectors: list[str]) -> bool:
    return await _first_visible_locator(page, selectors) is not None


async def _upload_resume(page, resume_path: str) -> bool:
    uploaded = False
    file_inputs = page.locator("input[type='file']")
    try:
        count = await file_inputs.count()
    except Exception:
        return False
    for idx in range(count):
        control = file_inputs.nth(idx)
        try:
            await control.set_input_files(resume_path)
            uploaded = True
        except Exception:
            continue
    return uploaded


async def _save_debug_artifacts(page, base_dir: str, name: str) -> None:
    try:
        await page.screenshot(
            path=_debug_artifact_path(base_dir, f"{name}.png"),
            full_page=True,
        )
    except Exception:
        pass
    try:
        html = await page.content()
        with open(_debug_artifact_path(base_dir, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        pass


def apply(job: dict, resume_path: str, settings: dict) -> tuple[str, int] | None:
    job_url = normalize_job_url(job.get("job_url"))
    if not job_url:
        return None

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    profile = load_profile(base_dir)
    session_path = ensure_session(settings, "linkedin", "https://www.linkedin.com/login")
    if not session_path:
        session_path = get_session_path(base_dir, settings, "linkedin")
    if not os.path.exists(session_path):
        log("LinkedIn apply: missing session file. Save the LinkedIn session from the dashboard first.")
        return ("deferred", 0)
    headless = settings.get("app", {}).get("headless", False)

    async def _apply():
        playwright, browser, context = await open_context(headless=headless, storage_state_path=session_path)
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2500)

            current_url = (page.url or "").lower()
            if any(token in current_url for token in LOGIN_GUARDS):
                log(f"LinkedIn apply: authentication gate detected at {page.url}")
                await _save_debug_artifacts(page, base_dir, "linkedin_apply_auth")
                return ("deferred", 0)

            if await _has_visible(page, SUCCESS_SELECTORS):
                log("LinkedIn apply: role already shows as applied.")
                return ("applied", 1)

            if not await _click_first(page, EASY_APPLY_SELECTORS):
                log("LinkedIn apply: Easy Apply button not found.")
                await _save_debug_artifacts(page, base_dir, "linkedin_apply_no_button")
                return ("review", 0)

            await page.wait_for_timeout(1500)
            uploaded_resume = False

            for step in range(1, 8):
                current_url = (page.url or "").lower()
                if any(token in current_url for token in LOGIN_GUARDS):
                    log(f"LinkedIn apply: authentication gate detected during modal flow at {page.url}")
                    await _save_debug_artifacts(page, base_dir, "linkedin_apply_auth_step")
                    return ("deferred", 1)

                if await _has_visible(page, SUCCESS_SELECTORS):
                    await _click_first(page, DONE_SELECTORS)
                    log(f"LinkedIn apply: success detected after step {step}.")
                    return ("applied", 1)

                if not uploaded_resume and os.path.exists(resume_path):
                    if await _upload_resume(page, resume_path):
                        uploaded_resume = True
                        log(f"LinkedIn apply: uploaded resume on step {step}.")
                        await page.wait_for_timeout(1200)

                agent_result = await fill_application_form(
                    page,
                    profile,
                    job,
                    "linkedin",
                    scope_selectors=MODAL_SELECTORS,
                )
                if agent_result["filled_count"]:
                    log(
                        "LinkedIn apply agent: "
                        f"step={step} filled={agent_result['filled_count']} "
                        f"prompts={agent_result['filled_prompts']}"
                    )
                    await page.wait_for_timeout(1200)

                if await _click_first(page, SUBMIT_SELECTORS):
                    log(f"LinkedIn apply: clicked submit on step {step}.")
                    await page.wait_for_timeout(2200)
                    continue

                if await _click_first(page, NEXT_SELECTORS):
                    log(f"LinkedIn apply: advanced modal step {step}.")
                    await page.wait_for_timeout(1800)
                    continue

                if await _has_visible(page, ERROR_SELECTORS):
                    if agent_result["unresolved_prompts"]:
                        log(
                            "LinkedIn apply agent: unresolved prompts "
                            f"on step {step}: {agent_result['unresolved_prompts']}"
                        )
                    log(f"LinkedIn apply: validation error detected on step {step}.")
                    await _save_debug_artifacts(page, base_dir, "linkedin_apply_validation")
                    return ("review", 1)

                if not await _has_visible(page, MODAL_SELECTORS):
                    if await _has_visible(page, SUCCESS_SELECTORS):
                        log(f"LinkedIn apply: modal closed after successful submit on step {step}.")
                        return ("applied", 1)
                    log(f"LinkedIn apply: modal closed without success marker on step {step}.")
                    await _save_debug_artifacts(page, base_dir, "linkedin_apply_modal_closed")
                    return ("review", 1)

                if agent_result["unresolved_prompts"]:
                    log(
                        "LinkedIn apply agent: unresolved prompts "
                        f"on step {step}: {agent_result['unresolved_prompts']}"
                    )
                    await _save_debug_artifacts(page, base_dir, "linkedin_apply_unresolved_questions")
                    return ("review", 1)

                log(f"LinkedIn apply: unresolved modal state on step {step}.")
                await page.wait_for_timeout(1000)

            log("LinkedIn apply: reached step limit without submission.")
            await _save_debug_artifacts(page, base_dir, "linkedin_apply_step_limit")
            return ("review", 1)
        finally:
            await close_context(playwright, browser, context)

    return run(_apply())

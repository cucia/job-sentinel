import os

from src.ai.form_filler import fill_application_form
from src.core.config import load_profile
from src.core.async_runner import run
from src.core.browser import close_context, open_context
from src.core.logger import log
from src.core.session import ensure_session, get_session_path


APPLY_BUTTON_SELECTORS = [
    "button.apply-button",
    "a.apply-button",
    "button:has-text('Apply')",
    "button:has-text('Apply on company site')",
]
SUBMIT_BUTTON_SELECTORS = [
    "button#submit",
    "button[type='submit']",
    "button:has-text('Submit')",
    "button:has-text('Continue')",
    "button:has-text('Next')",
]
SUCCESS_SELECTORS = [
    "text=Applied",
    "text=Application submitted",
    "text=You have successfully applied",
]
FORM_SCOPES = [
    "div[role='dialog']",
    "form",
    ".apply-layer",
    ".chatbot_DrawerContentWrapper",
]


async def _first_visible(page, selectors: list[str]):
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


def apply(job: dict, resume_path: str, settings: dict) -> tuple[str, int] | None:
    job_url = job.get("job_url")
    if not job_url:
        return

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    profile = load_profile(base_dir)
    session_path = ensure_session(settings, "naukri", "https://www.naukri.com/nlogin/login")
    if not session_path:
        session_path = get_session_path(base_dir, settings, "naukri")
    if not os.path.exists(session_path):
        log("Naukri apply: missing session file. Save the Naukri session from the dashboard first.")
        return ("deferred", 0)
    headless = settings.get("app", {}).get("headless", False)
    browser_type = settings.get("app", {}).get("browser", "firefox")

    async def _apply():
        playwright, browser, context = await open_context(
            headless=headless,
            storage_state_path=session_path,
            browser_type=browser_type
        )
        try:
            page = await context.new_page()
            await page.goto(job_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            apply_button = await _first_visible(page, APPLY_BUTTON_SELECTORS)
            if not apply_button:
                return ("review", 0)

            try:
                await apply_button.click()
            except Exception:
                return ("review", 0)
            await page.wait_for_timeout(1500)

            easy_apply = 1
            for step in range(1, 7):
                file_input = await page.query_selector("input[type='file']")
                if file_input and os.path.exists(resume_path):
                    try:
                        await file_input.set_input_files(resume_path)
                        log(f"Naukri apply: uploaded resume on step {step}.")
                        await page.wait_for_timeout(1000)
                    except Exception:
                        pass

                agent_result = await fill_application_form(
                    page,
                    profile,
                    job,
                    "naukri",
                    scope_selectors=FORM_SCOPES,
                )
                if agent_result["filled_count"]:
                    log(
                        "Naukri apply agent: "
                        f"step={step} filled={agent_result['filled_count']} "
                        f"prompts={agent_result['filled_prompts']}"
                    )
                    await page.wait_for_timeout(1000)

                submit_button = await _first_visible(page, SUBMIT_BUTTON_SELECTORS)
                if submit_button:
                    try:
                        await submit_button.click()
                        await page.wait_for_timeout(1500)
                    except Exception:
                        pass

                if await _first_visible(page, SUCCESS_SELECTORS):
                    return ("applied", easy_apply)

                if agent_result["unresolved_prompts"]:
                    log(
                        "Naukri apply agent: unresolved prompts "
                        f"on step {step}: {agent_result['unresolved_prompts']}"
                    )
                    return ("review", easy_apply)

            return ("review", easy_apply)
        finally:
            await close_context(playwright, browser, context)

    return run(_apply())

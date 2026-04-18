import os

from src.core.async_runner import run
from src.core.browser import close_context, open_context
from src.core.logger import log
from src.core.session import ensure_session, get_session_path


def apply(job: dict, resume_path: str, settings: dict) -> tuple[str, int] | None:
    job_url = job.get("job_url")
    if not job_url:
        return None

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    session_path = ensure_session(settings, "indeed", "https://www.indeed.com/account/login")
    if not session_path:
        session_path = get_session_path(base_dir, settings, "indeed")
    if not os.path.exists(session_path):
        log("Indeed apply: missing session file. Save the Indeed session from the dashboard first.")
        return ("deferred", 0)
    headless = settings.get("app", {}).get("headless", False)

    async def _apply():
        playwright, browser, context = await open_context(headless=headless, storage_state_path=session_path)
        try:
            page = await context.new_page()
            await page.goto(job_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            apply_button = await page.query_selector("button:has-text('Apply'), a:has-text('Apply')")
            if not apply_button:
                return ("review", 0)

            try:
                await apply_button.scroll_into_view_if_needed()
                if not await apply_button.is_visible():
                    return ("review", 0)
                await apply_button.click()
            except Exception:
                return ("review", 0)
            await page.wait_for_timeout(1500)

            file_input = await page.query_selector("input[type='file']")
            if file_input and os.path.exists(resume_path):
                await file_input.set_input_files(resume_path)
                await page.wait_for_timeout(1000)

            submit_button = await page.query_selector("button:has-text('Submit')")
            if submit_button:
                await submit_button.click()
                await page.wait_for_timeout(1000)
                return ("applied", 1)

            return ("review", 1)
        finally:
            await close_context(playwright, browser, context)

    return run(_apply())

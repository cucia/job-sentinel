import os

from core.browser import open_context, close_context
from core.session import ensure_session, get_session_path


def apply(job: dict, resume_path: str, settings: dict) -> None:
    job_url = job.get("job_url")
    if not job_url:
        return

    ensure_session(settings, "naukri", "https://www.naukri.com/nlogin/login")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    session_path = get_session_path(base_dir, settings, "naukri")
    headless = settings.get("app", {}).get("headless", False)

    playwright, browser, context = open_context(headless=headless, storage_state_path=session_path)
    try:
        page = context.new_page()
        page.goto(job_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        apply_button = page.query_selector("button.apply-button, a.apply-button")
        if not apply_button:
            return

        apply_button.click()
        page.wait_for_timeout(1500)

        file_input = page.query_selector("input[type='file']")
        if file_input and os.path.exists(resume_path):
            file_input.set_input_files(resume_path)
            page.wait_for_timeout(1000)

        submit_button = page.query_selector("button#submit, button[type='submit']")
        if submit_button:
            submit_button.click()
            page.wait_for_timeout(1000)
            return
    finally:
        close_context(playwright, browser, context)

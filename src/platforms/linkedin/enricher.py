import os

from src.core.async_runner import run
from src.core.browser import close_context, open_context
from src.core.logger import log
from src.core.session import ensure_session, get_session_path
from src.platforms.linkedin.url_utils import normalize_job_url


async def _first_text(page, selectors: list[str]) -> str:
    for sel in selectors:
        el = await page.query_selector(sel)
        if not el:
            continue
        text = (await el.text_content() or "").strip()
        if text:
            return text
    return ""


def enrich_job(job: dict, settings: dict) -> dict:
    job_url = normalize_job_url(job.get("job_url"))
    if not job_url:
        return {}

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    session_path = ensure_session(settings, "linkedin", "https://www.linkedin.com/login")
    if not session_path:
        session_path = get_session_path(base_dir, settings, "linkedin")
    if not os.path.exists(session_path):
        log("LinkedIn enrich: missing session file. Save the LinkedIn session from the dashboard first.")
        return {}
    headless = settings.get("app", {}).get("headless", False)

    async def _enrich():
        playwright, browser, context = await open_context(
            headless=headless,
            storage_state_path=session_path,
        )
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)

            description = await _first_text(
                page,
                [
                    "div.jobs-description__content",
                    "div.jobs-description-content__text",
                    "div.jobs-box__html-content",
                    "section#job-details",
                    "[data-test-job-description]",
                ],
            )

            company = await _first_text(
                page,
                [
                    "a.topcard__org-name-link",
                    "span.jobs-unified-top-card__company-name",
                    "a.jobs-unified-top-card__company-name",
                ],
            )

            location = await _first_text(
                page,
                [
                    "span.topcard__flavor--bullet",
                    "span.jobs-unified-top-card__bullet",
                    "span.jobs-unified-top-card__primary-description",
                ],
            )

            log(
                "LinkedIn enrich: "
                f"description_len={len(description)} company={'yes' if company else 'no'} "
                f"location={'yes' if location else 'no'}"
            )

            return {
                "description": description,
                "company": company,
                "location": location,
            }
        finally:
            await close_context(playwright, browser, context)

    return run(_enrich())

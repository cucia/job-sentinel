import os

from core.async_runner import run
from core.browser import close_context, open_context
from core.logger import log
from core.session import ensure_session, get_session_path


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
    job_url = (job.get("job_url") or "").strip()
    if not job_url:
        return {}

    ensure_session(settings, "linkedin", "https://www.linkedin.com/login")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    session_path = get_session_path(base_dir, settings, "linkedin")
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

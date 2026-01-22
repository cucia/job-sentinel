import os
from urllib.parse import quote_plus

from core.browser import open_context, close_context
from core.session import ensure_session, get_session_path


def _text_or_empty(el) -> str:
    if not el:
        return ""
    return (el.text_content() or "").strip()


def collect_jobs(settings: dict, profile: dict) -> list:
    platform_settings = settings.get("platforms", {}).get("linkedin", {})
    search = platform_settings.get("search", {})
    keywords = search.get("keywords", [])
    location = search.get("location", "")
    max_results = int(search.get("max_results", 10))

    if not keywords:
        return []

    session_path = ensure_session(settings, "linkedin", "https://www.linkedin.com/login")

    headless = settings.get("app", {}).get("headless", False)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if not session_path:
        session_path = get_session_path(base_dir, settings, "linkedin")
        if not os.path.exists(session_path):
            return []

    query = quote_plus(" ".join(keywords))
    loc = quote_plus(location) if location else ""
    url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}"

    playwright, browser, context = open_context(headless=headless, storage_state_path=session_path)
    try:
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        items = page.query_selector_all("ul.jobs-search__results-list li, div.base-card")
        jobs: list = []
        for item in items:
            link_el = item.query_selector("a.base-card__full-link")
            title_el = item.query_selector("h3.base-search-card__title")
            company_el = item.query_selector("h4.base-search-card__subtitle")
            location_el = item.query_selector("span.job-search-card__location")

            job_url = link_el.get_attribute("href") if link_el else ""
            title = _text_or_empty(title_el)
            company = _text_or_empty(company_el)
            location_text = _text_or_empty(location_el)

            if not title or not job_url:
                continue

            jobs.append(
                {
                    "platform": "linkedin",
                    "title": title,
                    "company": company,
                    "location": location_text,
                    "description": "",
                    "job_url": job_url.split("?")[0],
                }
            )

            if len(jobs) >= max_results:
                break

        return jobs
    finally:
        close_context(playwright, browser, context)

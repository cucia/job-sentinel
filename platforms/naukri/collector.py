import os
from urllib.parse import quote_plus

from core.browser import open_context, close_context
from core.session import ensure_session, get_session_path


def _text_or_empty(el) -> str:
    if not el:
        return ""
    return (el.text_content() or "").strip()


def collect_jobs(settings: dict, profile: dict) -> list:
    platform_settings = settings.get("platforms", {}).get("naukri", {})
    search = platform_settings.get("search", {})
    keywords = search.get("keywords", [])
    location = search.get("location", "")
    max_results = int(search.get("max_results", 10))

    if not keywords:
        return []

    ensure_session(settings, "naukri", "https://www.naukri.com/nlogin/login")

    headless = settings.get("app", {}).get("headless", False)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    session_path = get_session_path(base_dir, settings, "naukri")

    query = "-".join([quote_plus(k).replace("+", "-") for k in keywords])
    loc = quote_plus(location) if location else ""
    url = f"https://www.naukri.com/{query}-jobs?location={loc}"

    playwright, browser, context = open_context(headless=headless, storage_state_path=session_path)
    try:
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        items = page.query_selector_all("article.jobTuple")
        jobs: list = []
        for item in items:
            title_el = item.query_selector("a.title")
            company_el = item.query_selector("a.subTitle")
            location_el = item.query_selector("span.locWdth")

            job_url = title_el.get_attribute("href") if title_el else ""
            title = _text_or_empty(title_el)
            company = _text_or_empty(company_el)
            location_text = _text_or_empty(location_el)

            if not title or not job_url:
                continue

            jobs.append(
                {
                    "platform": "naukri",
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

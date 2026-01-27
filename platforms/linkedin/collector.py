import os
from urllib.parse import quote_plus

from core.async_runner import run
from core.browser import open_context, close_context
from core.logger import log
from core.session import ensure_session, get_session_path


async def _text_or_empty(el) -> str:
    if not el:
        return ""
    return (await el.text_content() or "").strip()


def collect_jobs(settings: dict, profile: dict) -> list:
    platform_settings = settings.get("platforms", {}).get("linkedin", {})
    search = platform_settings.get("search", {})
    keywords = search.get("keywords", [])
    location = search.get("location", "")
    max_results = int(search.get("max_results", 10))
    tpr_seconds = int(search.get("tpr_seconds", 0))

    if not keywords:
        return []

    log("LinkedIn: starting collection")
    session_path = ensure_session(settings, "linkedin", "https://www.linkedin.com/login")

    headless = settings.get("app", {}).get("headless", False)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if not session_path:
        session_path = get_session_path(base_dir, settings, "linkedin")
    if not os.path.exists(session_path):
        return []

    query = quote_plus(" ".join(keywords))
    loc = quote_plus(location) if location else ""
    params = [f"keywords={query}", "origin=SWITCH_SEARCH_VERTICAL"]
    if loc:
        params.append(f"location={loc}")
    if tpr_seconds > 0:
        params.append(f"f_TPR=r{tpr_seconds}")
    url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}"
    log(f"LinkedIn: search url built (max_results={max_results})")

    async def _collect():
        playwright, browser, context = await open_context(headless=headless, storage_state_path=session_path)
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            items = await page.query_selector_all("ul.jobs-search__results-list li, div.base-card")
            jobs: list = []
            for item in items:
                link_el = await item.query_selector("a.base-card__full-link")
                title_el = await item.query_selector("h3.base-search-card__title")
                company_el = await item.query_selector("h4.base-search-card__subtitle")
                location_el = await item.query_selector("span.job-search-card__location")

                job_url = await link_el.get_attribute("href") if link_el else ""
                title = await _text_or_empty(title_el)
                company = await _text_or_empty(company_el)
                location_text = await _text_or_empty(location_el)

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

            if not jobs:
                log(f"LinkedIn: no jobs found, title={await page.title()} url={page.url}")
                if "login" in page.url or "checkpoint" in page.url or "authwall" in page.url:
                    log("LinkedIn: likely not authenticated")
                try:
                    await page.screenshot(path="/app/data/linkedin_debug.png", full_page=True)
                    html = await page.content()
                    with open("/app/data/linkedin_debug.html", "w", encoding="utf-8") as f:
                        f.write(html)
                except Exception:
                    pass
            log(f"LinkedIn: collected {len(jobs)} jobs")
            return jobs
        finally:
            await close_context(playwright, browser, context)

    return run(_collect())

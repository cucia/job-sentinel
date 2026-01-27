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
    platform_settings = settings.get("platforms", {}).get("naukri", {})
    search = platform_settings.get("search", {})
    keywords = search.get("keywords", [])
    location = search.get("location", "")
    max_results = int(search.get("max_results", 10))

    if not keywords:
        return []

    log("Naukri: starting collection")
    session_path = ensure_session(settings, "naukri", "https://www.naukri.com/nlogin/login")

    headless = settings.get("app", {}).get("headless", False)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if not session_path:
        session_path = get_session_path(base_dir, settings, "naukri")
        if not os.path.exists(session_path):
            return []

    query = "-".join([quote_plus(k).replace("+", "-") for k in keywords])
    loc = quote_plus(location) if location else ""
    url = f"https://www.naukri.com/{query}-jobs?location={loc}"

    async def _collect():
        playwright, browser, context = await open_context(headless=headless, storage_state_path=session_path)
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(1000)

            items = await page.query_selector_all("article.jobTuple, div.jobTuple")
            jobs: list = []
            for item in items:
                title_el = await item.query_selector("a.title")
                company_el = await item.query_selector("a.subTitle")
                location_el = await item.query_selector("span.locWdth")

                job_url = await title_el.get_attribute("href") if title_el else ""
                title = await _text_or_empty(title_el)
                company = await _text_or_empty(company_el)
                location_text = await _text_or_empty(location_el)

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

            if not jobs:
                log(f"Naukri: no jobs found, title={await page.title()} url={page.url}")
                try:
                    await page.screenshot(path="/app/data/naukri_debug.png", full_page=True)
                except Exception:
                    pass
            log(f"Naukri: collected {len(jobs)} jobs")
            return jobs
        finally:
            await close_context(playwright, browser, context)

    return run(_collect())

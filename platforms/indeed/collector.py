import os
from urllib.parse import quote_plus

from core.async_runner import run
from core.browser import open_context, close_context
from core.logger import log
from core.session import ensure_session, get_session_path


def collect_jobs(settings: dict, profile: dict) -> list:
    platform_settings = settings.get("platforms", {}).get("indeed", {})
    search = platform_settings.get("search", {})
    keywords = search.get("keywords", [])
    location = search.get("location", "")
    max_results = int(search.get("max_results", 10))

    if not keywords:
        return []

    log("Indeed: starting collection")
    session_path = ensure_session(settings, "indeed", "https://www.indeed.com/account/login")

    headless = settings.get("app", {}).get("headless", False)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if not session_path:
        session_path = get_session_path(base_dir, settings, "indeed")
        if not os.path.exists(session_path):
            return []

    query = quote_plus(" ".join(keywords))
    loc = quote_plus(location) if location else ""
    url = f"https://www.indeed.com/jobs?q={query}&l={loc}"

    async def _collect():
        playwright, browser, context = await open_context(headless=headless, storage_state_path=session_path)
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            items = await page.query_selector_all("a[href*='/viewjob']")
            jobs: list = []
            seen = set()
            for link in items:
                href = await link.get_attribute("href") or ""
                if not href:
                    continue
                job_url = href
                if job_url.startswith("/"):
                    job_url = f"https://www.indeed.com{job_url}"
                job_url = job_url.split("&")[0]
                if job_url in seen:
                    continue
                seen.add(job_url)

                title = (await link.text_content() or "").strip() or "Indeed job"
                jobs.append(
                    {
                        "platform": "indeed",
                        "title": title,
                        "company": "",
                        "location": "",
                        "description": "",
                        "job_url": job_url,
                    }
                )
                if len(jobs) >= max_results:
                    break

            log(f"Indeed: collected {len(jobs)} jobs")
            return jobs
        finally:
            await close_context(playwright, browser, context)

    return run(_collect())

import os
from urllib.parse import quote_plus

from src.core.async_runner import run
from src.core.browser import close_context, open_context
from src.core.logger import log
from src.core.session import ensure_session, get_session_path


async def _text_or_empty(el) -> str:
    if not el:
        return ""
    return (await el.text_content() or "").strip()


def _debug_artifact_path(base_dir: str, filename: str) -> str:
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, filename)


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

    query = "-".join(quote_plus(keyword).replace("+", "-") for keyword in keywords)
    loc = quote_plus(location) if location else ""
    url = f"https://www.naukri.com/{query}-jobs?location={loc}"

    async def _collect():
        playwright, browser, context = await open_context(
            headless=headless,
            storage_state_path=session_path,
        )
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(2000)

            # Try multiple selector patterns for job cards
            items = await page.query_selector_all("article.jobTuple, div.jobTuple, div[class*='jobTuple'], article[class*='job'], div.srp-jobtuple-wrapper")
            log(f"Naukri: found {len(items)} potential job items")

            jobs: list = []
            seen = set()
            for item in items:
                # Try multiple selector patterns for title
                title_el = await item.query_selector("a.title, a[class*='title'], h2 a, h3 a, a.job-title")
                company_el = await item.query_selector("a.subTitle, a[class*='subTitle'], a.comp-name, span.comp-name, div.comp-name")
                location_el = await item.query_selector("span.locWdth, span.loc-wrap, span[class*='location'], li.location, span.location")
                time_el = await item.query_selector("span.job-post-day, span.job-posted, span.type, span[class*='posted']")

                job_url = await title_el.get_attribute("href") if title_el else ""
                if not job_url:
                    continue
                job_url = job_url.split("?")[0]
                if job_url in seen:
                    continue
                seen.add(job_url)

                title = await _text_or_empty(title_el)
                if not title:
                    continue

                jobs.append(
                    {
                        "platform": "naukri",
                        "title": title,
                        "company": await _text_or_empty(company_el),
                        "location": await _text_or_empty(location_el),
                        "description": "",
                        "job_url": job_url,
                        "posted_at": None,
                        "posted_text": await _text_or_empty(time_el) or None,
                    }
                )

                if len(jobs) >= max_results:
                    break

            if not jobs:
                log(f"Naukri: no jobs found, title={await page.title()} url={page.url}")
                try:
                    await page.screenshot(
                        path=_debug_artifact_path(base_dir, "naukri_debug.png"),
                        full_page=True,
                    )
                except Exception:
                    pass

            log(f"Naukri: collected {len(jobs)} jobs")
            return jobs
        finally:
            await close_context(playwright, browser, context)

    return run(_collect())

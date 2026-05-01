import os
from urllib.parse import quote_plus

from src.core.async_runner import run
from src.core.browser import open_context, close_context
from src.core.logger import log
from src.core.session import ensure_session, get_session_path


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
    browser_type = settings.get("app", {}).get("browser", "firefox")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if not session_path:
        session_path = get_session_path(base_dir, settings, "indeed")
        if not os.path.exists(session_path):
            return []

    query = quote_plus(" ".join(keywords))
    loc = quote_plus(location) if location else ""

    # Try Indeed RSS feed first (bypasses Cloudflare)
    rss_url = f"https://www.indeed.com/rss?q={query}&l={loc}"
    url = f"https://www.indeed.com/jobs?q={query}&l={loc}"

    async def _collect():
        playwright, browser, context = await open_context(
            headless=headless,
            storage_state_path=session_path,
            browser_type=browser_type
        )
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)

            # Try RSS feed first (no Cloudflare)
            log(f"Indeed: trying RSS feed first")
            await page.goto(rss_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            page_content = await page.content()

            # Check if RSS feed worked (contains XML)
            if "<rss" in page_content.lower() or "<feed" in page_content.lower():
                log(f"Indeed: RSS feed accessible, parsing jobs")
                # Parse RSS feed for job links
                items = await page.query_selector_all("item link, entry link")
                if len(items) > 0:
                    log(f"Indeed: found {len(items)} jobs from RSS feed")
                    jobs = []
                    seen = set()
                    for item in items[:max_results]:
                        link_text = await item.text_content()
                        if link_text and link_text not in seen:
                            seen.add(link_text)
                            jobs.append({
                                "platform": "indeed",
                                "title": "Indeed job",
                                "company": "",
                                "location": location,
                                "description": "",
                                "job_url": link_text.strip(),
                                "posted_at": None,
                                "posted_text": None,
                            })
                    log(f"Indeed: collected {len(jobs)} jobs from RSS")
                    return jobs

            # RSS failed, try regular page
            log(f"Indeed: RSS not available, trying regular page")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait longer for Cloudflare challenge to complete
            await page.wait_for_timeout(5000)

            # Check if we're still on Cloudflare challenge page
            page_title = await page.title()
            if "Just a moment" in page_title or "Cloudflare" in page_title:
                log(f"Indeed: Cloudflare challenge detected, waiting...")
                # Wait up to 15 seconds for challenge to complete
                for i in range(15):
                    await page.wait_for_timeout(1000)
                    page_title = await page.title()
                    if "Just a moment" not in page_title and "Cloudflare" not in page_title:
                        log(f"Indeed: Cloudflare challenge passed after {i+1} seconds")
                        break

            # Additional wait after page load
            await page.wait_for_timeout(2000)

            # Debug: log page title and URL
            page_title = await page.title()
            log(f"Indeed: page loaded, title={page_title} url={page.url}")

            # Try multiple selector patterns for job links
            items = await page.query_selector_all("a[href*='/viewjob'], a[href*='/rc/clk'], a[data-jk], h2.jobTitle a, a.jcs-JobTitle")
            log(f"Indeed: found {len(items)} potential job links")

            # If no items found, try to save a screenshot for debugging
            if len(items) == 0:
                try:
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                    data_dir = os.path.join(base_dir, "data")
                    os.makedirs(data_dir, exist_ok=True)
                    await page.screenshot(path=os.path.join(data_dir, "indeed_debug.png"), full_page=True)
                    log(f"Indeed: saved debug screenshot to data/indeed_debug.png")
                except Exception as e:
                    log(f"Indeed: failed to save screenshot: {e}")

            jobs: list = []
            seen = set()
            for link in items:
                # Try to find the job card container
                card = await link.evaluate_handle(
                    "el => el.closest('div.job_seen_beacon') || el.closest('div.cardOutline') || el.closest('div.jobsearch-SerpJobCard') || el.closest('li') || el.closest('div.slider_container') || el.closest('td.resultContent')"
                )
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
                company = ""
                location_text = ""
                posted_text = None
                posted_at = None
                if card:
                    company_el = await card.query_selector("span.companyName, a[data-testid='company-name'], span[data-testid='company-name'], div.company_location span")
                    location_el = await card.query_selector("div.companyLocation, span.companyLocation, div[data-testid='text-location'], div.company_location div")
                    time_el = await card.query_selector("span.date, time, span[data-testid='myJobsStateDate']")
                    company = (await company_el.text_content() or "").strip() if company_el else ""
                    location_text = (await location_el.text_content() or "").strip() if location_el else ""
                    posted_text = (await time_el.text_content() or "").strip() if time_el else None
                    posted_at = await time_el.get_attribute("datetime") if time_el else None
                jobs.append(
                    {
                        "platform": "indeed",
                        "title": title,
                        "company": company,
                        "location": location_text,
                        "description": "",
                        "job_url": job_url,
                        "posted_at": posted_at,
                        "posted_text": posted_text,
                    }
                )
                if len(jobs) >= max_results:
                    break

            log(f"Indeed: collected {len(jobs)} jobs")
            return jobs
        finally:
            await close_context(playwright, browser, context)

    return run(_collect())

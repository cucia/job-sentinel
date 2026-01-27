import os
from urllib.parse import quote_plus, urljoin

from core.async_runner import run
from core.browser import open_context, close_context
from core.logger import log
from core.session import ensure_session, get_session_path


async def _text_or_empty(el) -> str:
    if not el:
        return ""
    return (await el.text_content() or "").strip()


async def _card_details_from_link(link) -> tuple[str, str]:
    # Try to resolve company/location from the job card that contains the link.
    card = await link.evaluate_handle(
        "el => el.closest('li, article, div.jobs-search-results__list-item')"
    )
    if not card:
        return "", ""

    company_el = await card.query_selector(
        "h4, .base-search-card__subtitle, .job-card-container__company-name, a.app-aware-link"
    )
    location_el = await card.query_selector(
        ".job-search-card__location, .base-search-card__metadata, .job-card-container__metadata-item"
    )

    company = await _text_or_empty(company_el)
    location = await _text_or_empty(location_el)
    return company, location


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
    session_exists = os.path.exists(session_path)
    session_size = os.path.getsize(session_path) if session_exists else 0
    log(f"LinkedIn: session_path={session_path} exists={session_exists} size={session_size}")
    if not session_exists:
        return []

    query = quote_plus(" ".join(keywords))
    loc = quote_plus(location) if location else ""
    params = [f"keywords={query}", "origin=SWITCH_SEARCH_VERTICAL"]
    if loc:
        params.append(f"location={loc}")
    if tpr_seconds > 0:
        params.append(f"f_TPR=r{tpr_seconds}")
    url = f"https://www.linkedin.com/jobs/search-results/?{'&'.join(params)}"
    log(f"LinkedIn: search url built (max_results={max_results}, tpr_seconds={tpr_seconds})")

    async def _collect():
        playwright, browser, context = await open_context(headless=headless, storage_state_path=session_path)
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            jobs: list = []
            seen = set()
            stagnant_rounds = 0
            last_seen_count = 0
            scroll_box = await page.query_selector(
                "div.jobs-search-results-list, div.scaffold-layout__list"
            )

            while len(seen) < max_results and stagnant_rounds < 6:
                links = await page.query_selector_all("a[href*='/jobs/view/']")
                before_count = len(seen)
                for link in links:
                    href = await link.get_attribute("href") or ""
                    if not href:
                        continue
                    job_url = urljoin("https://www.linkedin.com", href.split("?")[0])
                    if job_url in seen:
                        continue
                    seen.add(job_url)

                    title = (await link.get_attribute("aria-label") or await link.text_content() or "").strip()
                    if not title:
                        title = "LinkedIn job"

                    company, location_text = await _card_details_from_link(link)

                    jobs.append(
                        {
                            "platform": "linkedin",
                            "title": title,
                            "company": company,
                            "location": location_text,
                            "description": "",
                            "job_url": job_url,
                        }
                    )

                    if len(jobs) >= max_results:
                        break
                after_count = len(seen)
                log(
                    "LinkedIn scroll: "
                    f"anchors={len(links)} new={after_count - before_count} total={after_count}"
                )

                if len(seen) == last_seen_count:
                    stagnant_rounds += 1
                else:
                    stagnant_rounds = 0
                last_seen_count = len(seen)

                # Scroll the results list to load more jobs.
                if scroll_box:
                    await scroll_box.evaluate("el => el.scrollBy(0, el.scrollHeight)")
                else:
                    await page.mouse.wheel(0, 2500)

                # Click "Show more jobs" if present.
                show_more = await page.query_selector("button:has-text('Show more jobs')")
                if show_more and await show_more.is_visible():
                    try:
                        await show_more.click()
                    except Exception:
                        pass

                await page.wait_for_timeout(1200)

            log(
                "LinkedIn: search summary: "
                f"unique_links={len(seen)} collected={len(jobs)} "
                f"max_results={max_results} stagnant_rounds={stagnant_rounds}"
            )

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

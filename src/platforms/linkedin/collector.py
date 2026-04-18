import os
from urllib.parse import quote_plus

from src.core.async_runner import run
from src.core.browser import open_context, close_context
from src.core.logger import log
from src.core.session import ensure_session, get_session_path
from src.platforms.linkedin.url_utils import normalize_job_url


async def _text_or_empty(el) -> str:
    if not el:
        return ""
    return (await el.text_content() or "").strip()


async def _first_selector(page, selectors):
    for selector in selectors:
        el = await page.query_selector(selector)
        if el:
            return el
    return None


async def _posted_info(item):
    time_el = await item.query_selector("time")
    if not time_el:
        return None, None
    posted_text = (await time_el.text_content() or "").strip() or None
    posted_at = await time_el.get_attribute("datetime") or None
    return posted_at, posted_text


async def _easy_apply_flag(item) -> int:
    selectors = [
        ".job-card-container__apply-method",
        ".job-card-list__footer-wrapper",
        ".job-card-container__footer-wrapper",
        ".job-card-container__footer-item",
        ".job-card-list__footer-wrapper li",
    ]
    for selector in selectors:
        elements = await item.query_selector_all(selector)
        for el in elements:
            text = (await el.text_content() or "").strip().lower()
            if "easy apply" in text:
                return 1
    try:
        text = ((await item.text_content()) or "").lower()
    except Exception:
        text = ""
    return 1 if "easy apply" in text else 0


def _debug_artifact_path(base_dir: str, filename: str) -> str:
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, filename)


def collect_jobs(settings: dict, profile: dict) -> list:
    platform_settings = settings.get("platforms", {}).get("linkedin", {})
    search = platform_settings.get("search", {})
    keywords = search.get("keywords", [])
    location = search.get("location", "")
    max_results = int(search.get("max_results", 10))
    tpr_seconds = int(search.get("tpr_seconds", 0))
    easy_apply_only = bool(search.get("easy_apply_only", False))

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
    if easy_apply_only:
        params.append("f_AL=true")
    url = f"https://www.linkedin.com/jobs/search/?{'&'.join(params)}"
    log(
        "LinkedIn: search url built "
        f"(max_results={max_results} easy_apply_only={easy_apply_only})"
    )

    async def _collect():
        playwright, browser, context = await open_context(headless=headless, storage_state_path=session_path)
        try:
            page = await context.new_page()
            page.set_default_timeout(30000)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            jobs: list = []
            seen = set()
            easy_apply_count = 0

            await page.wait_for_selector(
                "li[data-occludable-job-id], ul.jobs-search__results-list li, div.base-card",
                timeout=15000,
            )

            result_count_el = await _first_selector(
                page,
                [
                    "span.results-context-header__job-count",
                    "span.jobs-search-results-list__text",
                    "small.jobs-search-results-list__text",
                ],
            )
            if result_count_el:
                log(f"LinkedIn: results text={await _text_or_empty(result_count_el)}")

            list_container = await _first_selector(
                page,
                [
                    "div.scaffold-layout__list-container",
                    "div.jobs-search-results-list",
                    "div.jobs-search-results__list",
                    "ul.scaffold-layout__list-container",
                    "ul.jobs-search__results-list",
                ],
            )

            max_rounds = max(10, min(100, max_results * 4))
            stagnant_rounds = 0

            # Newer LinkedIn UI (two-pane jobs search)
            for _ in range(max_rounds):
                items = await page.query_selector_all("li[data-occludable-job-id]")
                new_count = 0
                for item in items:
                    link_el = await item.query_selector("a[href*='/jobs/view/']")
                    job_url = await link_el.get_attribute("href") if link_el else ""
                    if not job_url:
                        continue
                    job_url = normalize_job_url(job_url)
                    if job_url in seen:
                        continue
                    seen.add(job_url)
                    new_count += 1

                    title_el = await item.query_selector("a.job-card-list__title, a.job-card-container__link")
                    company_el = await item.query_selector(".job-card-container__company-name, .job-card-container__primary-description")
                    location_el = await item.query_selector(".job-card-container__metadata-item, .job-card-container__metadata-wrapper")

                    title = await _text_or_empty(title_el)
                    company = await _text_or_empty(company_el)
                    location_text = await _text_or_empty(location_el)
                    posted_at, posted_text = await _posted_info(item)
                    easy_apply = await _easy_apply_flag(item)
                    if easy_apply_only and not easy_apply:
                        continue

                    jobs.append(
                        {
                            "platform": "linkedin",
                            "title": title or "LinkedIn job",
                            "company": company,
                            "location": location_text,
                            "description": "",
                            "job_url": job_url,
                            "easy_apply": easy_apply,
                            "posted_at": posted_at,
                            "posted_text": posted_text,
                        }
                    )
                    easy_apply_count += easy_apply
                    if len(jobs) >= max_results:
                        break

                log(f"LinkedIn scroll: items={len(items)} new={new_count} total={len(seen)}")

                if len(jobs) >= max_results:
                    break

                if new_count == 0:
                    stagnant_rounds += 1
                else:
                    stagnant_rounds = 0

                if stagnant_rounds >= 6:
                    break

                if list_container:
                    await page.evaluate("el => { el.scrollBy(0, el.scrollHeight); }", list_container)
                else:
                    await page.mouse.wheel(0, 2000)
                    await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1200)

            log(
                "LinkedIn: search summary: "
                f"unique_links={len(seen)} collected={len(jobs)} "
                f"easy_apply={easy_apply_count} "
                f"max_results={max_results} stagnant_rounds={stagnant_rounds}"
            )

            # Fallback to older UI selectors
            if not jobs:
                items = await page.query_selector_all("ul.jobs-search__results-list li, div.base-card")
                log(f"LinkedIn: fallback items found={len(items)}")
                for item in items:
                    link_el = await item.query_selector("a.base-card__full-link")
                    title_el = await item.query_selector("h3.base-search-card__title")
                    company_el = await item.query_selector("h4.base-search-card__subtitle")
                    location_el = await item.query_selector("span.job-search-card__location")
                    time_el = await item.query_selector("time")

                    job_url = await link_el.get_attribute("href") if link_el else ""
                    job_url = normalize_job_url(job_url)
                    title = await _text_or_empty(title_el)
                    company = await _text_or_empty(company_el)
                    location_text = await _text_or_empty(location_el)
                    posted_text = await _text_or_empty(time_el) or None
                    posted_at = await time_el.get_attribute("datetime") if time_el else None
                    easy_apply = await _easy_apply_flag(item)
                    if easy_apply_only and not easy_apply:
                        continue

                    if not title or not job_url:
                        continue

                    jobs.append(
                        {
                            "platform": "linkedin",
                            "title": title,
                            "company": company,
                            "location": location_text,
                            "description": "",
                            "job_url": job_url,
                            "easy_apply": easy_apply,
                            "posted_at": posted_at,
                            "posted_text": posted_text,
                        }
                    )
                    easy_apply_count += easy_apply

                    if len(jobs) >= max_results:
                        break

            if not jobs:
                log(f"LinkedIn: no jobs found, title={await page.title()} url={page.url}")
                if "login" in page.url or "checkpoint" in page.url or "authwall" in page.url:
                    log("LinkedIn: likely not authenticated")
                try:
                    await page.screenshot(
                        path=_debug_artifact_path(base_dir, "linkedin_debug.png"),
                        full_page=True,
                    )
                    html = await page.content()
                    with open(_debug_artifact_path(base_dir, "linkedin_debug.html"), "w", encoding="utf-8") as f:
                        f.write(html)
                except Exception:
                    pass
            log(f"LinkedIn: collected {len(jobs)} jobs")
            return jobs
        finally:
            await close_context(playwright, browser, context)

    return run(_collect())

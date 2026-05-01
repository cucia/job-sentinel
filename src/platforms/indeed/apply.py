import os
import random

from src.core.async_runner import run
from src.core.browser import close_context, open_context
from src.core.logger import log
from src.core.session import ensure_session, get_session_path


async def human_delay(page, min_ms: int = 500, max_ms: int = 2000):
    """Add random human-like delay"""
    await page.wait_for_timeout(random.randint(min_ms, max_ms))


async def smooth_scroll(page, selector: str):
    """Scroll to element smoothly like a human"""
    try:
        element = await page.query_selector(selector)
        if element:
            box = await element.bounding_box()
            if box:
                # Scroll in steps
                current_y = await page.evaluate("window.pageYOffset")
                target_y = box['y'] - 100
                steps = random.randint(3, 6)
                step_size = (target_y - current_y) / steps

                for _ in range(steps):
                    await page.evaluate(f"window.scrollBy(0, {step_size})")
                    await page.wait_for_timeout(random.randint(50, 150))
    except Exception:
        pass


def apply(job: dict, resume_path: str, settings: dict) -> tuple[str, int] | None:
    job_url = job.get("job_url")
    if not job_url:
        return None

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    session_path = ensure_session(settings, "indeed", "https://www.indeed.com/account/login")
    if not session_path:
        session_path = get_session_path(base_dir, settings, "indeed")
    if not os.path.exists(session_path):
        log("Indeed apply: missing session file. Save the Indeed session from the dashboard first.")
        return ("deferred", 0)
    headless = settings.get("app", {}).get("headless", False)
    browser_type = settings.get("app", {}).get("browser", "firefox")

    async def _apply():
        playwright, browser, context = await open_context(
            headless=headless,
            storage_state_path=session_path,
            browser_type=browser_type
        )
        try:
            page = await context.new_page()

            # Navigate with random delay
            await page.goto(job_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(2000, 4000))

            # Random mouse movements to simulate human behavior
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            await page.wait_for_timeout(random.randint(300, 800))

            # Look for apply button with multiple selectors
            apply_selectors = [
                "button:has-text('Apply')",
                "a:has-text('Apply')",
                "button[data-testid*='apply']",
                "a[data-testid*='apply']",
                ".jobsearch-IndeedApplyButton",
                "#indeedApplyButton"
            ]

            apply_button = None
            for selector in apply_selectors:
                apply_button = await page.query_selector(selector)
                if apply_button:
                    break

            if not apply_button:
                log(f"Indeed apply: No apply button found for {job_url}")
                return ("review", 0)

            # Smooth scroll to button
            await smooth_scroll(page, selector)
            await page.wait_for_timeout(random.randint(500, 1000))

            try:
                if not await apply_button.is_visible():
                    log(f"Indeed apply: Apply button not visible for {job_url}")
                    return ("review", 0)

                # Hover before clicking
                await apply_button.hover()
                await page.wait_for_timeout(random.randint(200, 500))
                await apply_button.click()
            except Exception as e:
                log(f"Indeed apply: Failed to click apply button: {e}")
                return ("review", 0)

            await page.wait_for_timeout(random.randint(1500, 3000))

            # Handle resume upload
            file_input = await page.query_selector("input[type='file']")
            if file_input and os.path.exists(resume_path):
                await file_input.set_input_files(resume_path)
                await page.wait_for_timeout(random.randint(1000, 2000))
                log(f"Indeed apply: Resume uploaded for {job_url}")

            # Look for submit button with multiple selectors
            submit_selectors = [
                "button:has-text('Submit')",
                "button:has-text('Submit application')",
                "button[type='submit']",
                "button[data-testid*='submit']",
                ".ia-continueButton"
            ]

            submit_button = None
            for selector in submit_selectors:
                submit_button = await page.query_selector(selector)
                if submit_button:
                    break

            if submit_button:
                await submit_button.hover()
                await page.wait_for_timeout(random.randint(300, 700))
                await submit_button.click()
                await page.wait_for_timeout(random.randint(2000, 4000))
                log(f"Indeed apply: Application submitted for {job_url}")
                return ("applied", 1)

            log(f"Indeed apply: No submit button found, needs review for {job_url}")
            return ("review", 1)
        except Exception as e:
            log(f"Indeed apply: Error during application: {e}")
            return ("review", 0)
        finally:
            await close_context(playwright, browser, context)

    return run(_apply())

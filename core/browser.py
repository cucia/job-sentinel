import os
from typing import Tuple

from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext


async def open_context(
    headless: bool,
    storage_state_path: str | None = None,
) -> Tuple[Playwright, Browser, BrowserContext]:
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)

    if storage_state_path and os.path.exists(storage_state_path):
        context = await browser.new_context(storage_state=storage_state_path)
    else:
        context = await browser.new_context()

    return playwright, browser, context


async def save_storage_state(context: BrowserContext, storage_state_path: str) -> None:
    os.makedirs(os.path.dirname(storage_state_path), exist_ok=True)
    await context.storage_state(path=storage_state_path)


async def close_context(playwright: Playwright, browser: Browser, context: BrowserContext) -> None:
    await context.close()
    await browser.close()
    await playwright.stop()

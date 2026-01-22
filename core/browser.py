import os
from typing import Tuple
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext


def open_context(headless: bool, storage_state_path: str | None = None) -> Tuple[Playwright, Browser, BrowserContext]:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)

    if storage_state_path and os.path.exists(storage_state_path):
        context = browser.new_context(storage_state=storage_state_path)
    else:
        context = browser.new_context()

    return playwright, browser, context


def save_storage_state(context: BrowserContext, storage_state_path: str) -> None:
    os.makedirs(os.path.dirname(storage_state_path), exist_ok=True)
    context.storage_state(path=storage_state_path)


def close_context(playwright: Playwright, browser: Browser, context: BrowserContext) -> None:
    context.close()
    browser.close()
    playwright.stop()

import os
from typing import Tuple

from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext


async def open_context(
    headless: bool,
    storage_state_path: str | None = None,
    browser_type: str = "firefox",
) -> Tuple[Playwright, Browser, BrowserContext]:
    """
    Open a browser context with anti-detection features.

    Args:
        headless: Run browser in headless mode
        storage_state_path: Path to saved session cookies
        browser_type: Browser to use - "firefox", "chromium", or "webkit"

    Returns:
        Tuple of (playwright, browser, context)
    """
    playwright = await async_playwright().start()

    # Launch browser based on type
    if browser_type == "firefox":
        browser = await playwright.firefox.launch(
            headless=headless,
            firefox_user_prefs={
                'dom.webdriver.enabled': False,
                'useAutomationExtension': False,
                'general.platform.override': 'Win32',
                'general.useragent.override': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
            }
        )
    elif browser_type == "webkit":
        browser = await playwright.webkit.launch(headless=headless)
    else:  # chromium (fallback)
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

    # Browser-specific anti-detection context settings
    if browser_type == "firefox":
        context_options = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation', 'notifications'],
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1'
            }
        }
    elif browser_type == "webkit":
        context_options = {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation', 'notifications'],
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
    else:  # chromium
        context_options = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation', 'notifications'],
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        }

    if storage_state_path and os.path.exists(storage_state_path):
        context_options['storage_state'] = storage_state_path

    context = await browser.new_context(**context_options)

    # Inject anti-detection scripts (browser-specific)
    if browser_type == "firefox":
        # Firefox-specific anti-detection
        await context.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });

            // Firefox-specific properties
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Firefox doesn't have chrome object, so don't add it
        """)
    elif browser_type == "chromium":
        # Chromium-specific anti-detection
        await context.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Chrome runtime
            window.chrome = {
                runtime: {}
            };

            // Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    # Webkit doesn't need much anti-detection as it's less scrutinized

    return playwright, browser, context


async def save_storage_state(context: BrowserContext, storage_state_path: str) -> None:
    os.makedirs(os.path.dirname(storage_state_path), exist_ok=True)
    await context.storage_state(path=storage_state_path)


async def close_context(playwright: Playwright, browser: Browser, context: BrowserContext) -> None:
    await context.close()
    await browser.close()
    await playwright.stop()

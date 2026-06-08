"""
Playwright Browser Adapter

Real browser automation using Playwright.
Implements BrowserAdapter interface for web automation.

Supports:
- Navigation to URLs
- Element finding and interaction
- Page analysis (title, HTML, URL)
- Screenshots
- Waiting for elements
"""

import logging
from typing import Optional, List
from backend.browser.adapter import BrowserAdapter
from backend.browser.page import BrowserPage
from backend.browser.element import BrowserElement
from backend.browser.result import BrowserResult

logger = logging.getLogger(__name__)


class PlaywrightBrowserElement(BrowserElement):
    """Playwright-backed browser element."""

    def __init__(self, locator, selector: str):
        """
        Initialize element backed by Playwright locator.

        Args:
            locator: Playwright Locator object
            selector: CSS selector
        """
        self.locator = locator
        self.selector = selector
        self._text = ""
        self._attributes = {}
        self._visible = True

    async def click(self) -> BrowserResult:
        """Click element."""
        try:
            if not await self.locator.is_visible():
                return BrowserResult(
                    success=False,
                    action="click",
                    selector=self.selector,
                    message="Element not visible",
                )

            await self.locator.click()
            return BrowserResult(
                success=True,
                action="click",
                selector=self.selector,
                message=f"Clicked {self.selector}",
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                action="click",
                selector=self.selector,
                message=f"Click failed: {str(e)}",
            )

    async def fill(self, value: str) -> BrowserResult:
        """Fill element with value."""
        try:
            # Note: We skip visibility check to support multi-step forms where
            # fields may be hidden via CSS (display: none) but still fillable.
            # Playwright can fill hidden fields programmatically with force: True.
            # For user interaction simulation, consider using force: True option.

            await self.locator.fill(value, force=True)
            self._attributes["value"] = value

            return BrowserResult(
                success=True,
                action="fill",
                selector=self.selector,
                message=f"Filled {self.selector}",
                metadata={"value_length": len(value)},
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                action="fill",
                selector=self.selector,
                message=f"Fill failed: {str(e)}",
            )

    async def get_text(self) -> str:
        """Get element text."""
        try:
            return await self.locator.text_content()
        except:
            return ""

    async def get_attribute(self, name: str) -> Optional[str]:
        """Get element attribute."""
        try:
            return await self.locator.get_attribute(name)
        except:
            return None

    async def input_value(self) -> str:
        """Get current input element value (reads from DOM, not attribute)."""
        try:
            # Use Playwright's input_value() to read the live DOM value
            # This works for <input>, <textarea>, and <select> elements
            return await self.locator.input_value()
        except Exception as e:
            # Fallback: try to read value attribute
            try:
                value = await self.locator.get_attribute("value")
                return value or ""
            except:
                return ""

    async def select_option(self, value: str) -> "BrowserResult":
        """Select option in a <select> element."""
        try:
            # Note: Skip visibility check for multi-step forms where select elements
            # may be hidden. Use force: True to bypass Playwright's visibility checks.

            # Use Playwright's select_option() for <select> elements
            await self.locator.select_option(value, force=True)

            return BrowserResult(
                success=True,
                action="select_option",
                selector=self.selector,
                message=f"Selected option: {value}",
                metadata={"value": value},
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                action="select_option",
                selector=self.selector,
                message=f"Select failed: {str(e)}",
            )

    async def check(self) -> BrowserResult:
        """Check a checkbox element."""
        try:
            if not await self.locator.is_visible():
                return BrowserResult(
                    success=False,
                    action="check",
                    selector=self.selector,
                    message="Element not visible",
                )

            await self.locator.check()

            return BrowserResult(
                success=True,
                action="check",
                selector=self.selector,
                message=f"Checked {self.selector}",
                metadata={"checked": True},
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                action="check",
                selector=self.selector,
                message=f"Check failed: {str(e)}",
            )

    async def uncheck(self) -> BrowserResult:
        """Uncheck a checkbox element."""
        try:
            if not await self.locator.is_visible():
                return BrowserResult(
                    success=False,
                    action="uncheck",
                    selector=self.selector,
                    message="Element not visible",
                )

            await self.locator.uncheck()

            return BrowserResult(
                success=True,
                action="uncheck",
                selector=self.selector,
                message=f"Unchecked {self.selector}",
                metadata={"checked": False},
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                action="uncheck",
                selector=self.selector,
                message=f"Uncheck failed: {str(e)}",
            )

    async def upload_file(self, file_path: str) -> BrowserResult:
        """Upload file to file input element."""
        try:
            import os

            # Verify file exists
            if not os.path.exists(file_path):
                return BrowserResult(
                    success=False,
                    action="upload_file",
                    selector=self.selector,
                    message=f"File not found: {file_path}",
                )

            # Note: File inputs don't need to be visible for set_input_files() to work.
            # Playwright can set files on hidden file inputs, so we skip visibility check.
            # This is different from click() or fill() which require visibility.

            # Use Playwright's set_input_files() for file uploads
            await self.locator.set_input_files(file_path)

            logger.info(f"[PlaywrightAdapter] File uploaded: {file_path}")
            return BrowserResult(
                success=True,
                action="upload_file",
                selector=self.selector,
                message=f"Uploaded file: {file_path}",
                metadata={"file_path": file_path, "file_size": os.path.getsize(file_path)},
            )
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] File upload failed: {e}")
            return BrowserResult(
                success=False,
                action="upload_file",
                selector=self.selector,
                message=f"Upload failed: {str(e)}",
            )

    async def select_radio(self, value: str) -> BrowserResult:
        """Select a radio button option."""
        try:
            if not await self.locator.is_visible():
                return BrowserResult(
                    success=False,
                    action="select_radio",
                    selector=self.selector,
                    message="Element not visible",
                )

            # Find and check the radio with matching value
            radio_selector = f'{self.selector}[value="{value}"]'
            await self.locator.page.locator(radio_selector).check()

            return BrowserResult(
                success=True,
                action="select_radio",
                selector=self.selector,
                message=f"Selected radio option: {value}",
                metadata={"value": value},
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                action="select_radio",
                selector=self.selector,
                message=f"Select radio failed: {str(e)}",
            )


class PlaywrightAdapter(BrowserAdapter):
    """Playwright implementation of BrowserAdapter."""

    def __init__(self):
        """Initialize Playwright adapter."""
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.current_page_url = ""

    async def start(self) -> BrowserResult:
        """Start Playwright browser."""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()

            logger.info("[PlaywrightAdapter] Browser started")
            return BrowserResult(
                success=True,
                action="start",
                message="Playwright browser started",
            )
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] Failed to start: {e}")
            return BrowserResult(
                success=False,
                action="start",
                message=f"Failed to start browser: {str(e)}",
            )

    async def stop(self) -> BrowserResult:
        """Stop Playwright browser."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("[PlaywrightAdapter] Browser stopped")
            return BrowserResult(
                success=True,
                action="stop",
                message="Playwright browser stopped",
            )
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] Failed to stop: {e}")
            return BrowserResult(
                success=False,
                action="stop",
                message=f"Failed to stop browser: {str(e)}",
            )

    async def goto(self, url: str) -> BrowserResult:
        """Navigate to URL."""
        try:
            if not self.context:
                return BrowserResult(
                    success=False,
                    action="goto",
                    message="Browser not started",
                )

            # Create page from context if needed
            if not self.page:
                self.page = await self.context.new_page()

            await self.page.goto(url, wait_until="domcontentloaded")
            self.current_page_url = url

            logger.info(f"[PlaywrightAdapter] Navigated to {url}")
            return BrowserResult(
                success=True,
                action="goto",
                message=f"Navigated to {url}",
                metadata={"url": url},
            )
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] Navigation failed: {e}")
            return BrowserResult(
                success=False,
                action="goto",
                message=f"Navigation failed: {str(e)}",
                metadata={"url": url},
            )

    async def current_url(self) -> str:
        """Get current page URL."""
        try:
            if self.page:
                return self.page.url
            return self.current_page_url
        except:
            return self.current_page_url

    async def get_title(self) -> str:
        """Get page title."""
        try:
            if self.page:
                return await self.page.title()
            return ""
        except:
            return ""

    async def get_html(self) -> str:
        """Get page HTML."""
        try:
            if self.page:
                return await self.page.content()
            return ""
        except:
            return ""

    async def get_page(self) -> BrowserPage:
        """Get current page object."""
        try:
            url = await self.current_url()
            title = await self.get_title()
            html = await self.get_html()

            return BrowserPage(
                url=url,
                title=title,
                html=html,
            )
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] Failed to get page: {e}")
            return BrowserPage(
                url=self.current_page_url,
                title="",
                html="",
            )

    async def find_element(self, selector: str) -> Optional[PlaywrightBrowserElement]:
        """Find single element by selector."""
        try:
            if not self.page:
                return None

            locator = self.page.locator(selector)

            # Check if element exists
            count = await locator.count()
            if count == 0:
                return None

            return PlaywrightBrowserElement(locator, selector)
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] Find element failed: {e}")
            return None

    async def find_elements(self, selector: str) -> List[PlaywrightBrowserElement]:
        """Find multiple elements by selector."""
        try:
            if not self.page:
                return []

            locator = self.page.locator(selector)
            count = await locator.count()

            elements = []
            for i in range(count):
                element_locator = self.page.locator(selector).nth(i)
                element = PlaywrightBrowserElement(element_locator, f"{selector}[{i}]")
                elements.append(element)

            return elements
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] Find elements failed: {e}")
            return []

    async def wait_for_element(
        self, selector: str, timeout: int = 30
    ) -> Optional[PlaywrightBrowserElement]:
        """Wait for element to appear and be visible."""
        try:
            if not self.page:
                return None

            locator = self.page.locator(selector)
            await locator.wait_for(state="visible", timeout=timeout * 1000)

            return PlaywrightBrowserElement(locator, selector)
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] Wait for element failed: {e}")
            return None

    async def screenshot(self, path: str) -> BrowserResult:
        """Take a screenshot."""
        try:
            if not self.page:
                return BrowserResult(
                    success=False,
                    action="screenshot",
                    message="No page loaded",
                )

            await self.page.screenshot(path=path)

            logger.info(f"[PlaywrightAdapter] Screenshot saved to {path}")
            return BrowserResult(
                success=True,
                action="screenshot",
                message=f"Screenshot saved to {path}",
                metadata={"path": path},
            )
        except Exception as e:
            logger.error(f"[PlaywrightAdapter] Screenshot failed: {e}")
            return BrowserResult(
                success=False,
                action="screenshot",
                message=f"Screenshot failed: {str(e)}",
                metadata={"path": path},
            )

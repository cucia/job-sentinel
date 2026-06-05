"""
Browser Adapter

Abstract interface for browser implementations.
Implementation-independent: no Playwright, Selenium, or other framework imports.

Allows multiple implementations:
- MockBrowserAdapter (testing)
- PlaywrightAdapter (future)
- SeleniumAdapter (future)
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from backend.browser.page import BrowserPage
from backend.browser.element import BrowserElement
from backend.browser.result import BrowserResult


class BrowserAdapter(ABC):
    """Abstract browser adapter interface."""

    @abstractmethod
    async def start(self) -> BrowserResult:
        """
        Start the browser.

        Returns:
            BrowserResult indicating success
        """
        pass

    @abstractmethod
    async def stop(self) -> BrowserResult:
        """
        Stop the browser.

        Returns:
            BrowserResult indicating success
        """
        pass

    @abstractmethod
    async def goto(self, url: str) -> BrowserResult:
        """
        Navigate to URL.

        Args:
            url: URL to navigate to

        Returns:
            BrowserResult indicating success
        """
        pass

    @abstractmethod
    async def current_url(self) -> str:
        """
        Get current page URL.

        Returns:
            Current URL
        """
        pass

    @abstractmethod
    async def get_title(self) -> str:
        """
        Get page title.

        Returns:
            Page title
        """
        pass

    @abstractmethod
    async def get_html(self) -> str:
        """
        Get page HTML.

        Returns:
            Page HTML content
        """
        pass

    @abstractmethod
    async def get_page(self) -> BrowserPage:
        """
        Get current page object.

        Returns:
            BrowserPage with current page data
        """
        pass

    @abstractmethod
    async def find_element(self, selector: str) -> Optional[BrowserElement]:
        """
        Find single element by selector.

        Args:
            selector: CSS selector

        Returns:
            BrowserElement or None if not found
        """
        pass

    @abstractmethod
    async def find_elements(self, selector: str) -> List[BrowserElement]:
        """
        Find multiple elements by selector.

        Args:
            selector: CSS selector

        Returns:
            List of BrowserElement objects
        """
        pass

    @abstractmethod
    async def wait_for_element(self, selector: str, timeout: int = 30) -> Optional[BrowserElement]:
        """
        Wait for element to appear.

        Args:
            selector: CSS selector
            timeout: Timeout in seconds

        Returns:
            BrowserElement when found, None if timeout
        """
        pass

    @abstractmethod
    async def screenshot(self, path: str) -> BrowserResult:
        """
        Take a screenshot.

        Args:
            path: File path to save screenshot

        Returns:
            BrowserResult indicating success
        """
        pass


class MockBrowserAdapter(BrowserAdapter):
    """Mock browser adapter for testing (no real browser required)."""

    def __init__(self):
        """Initialize mock adapter."""
        self.is_started = False
        self.current_page_url = ""
        self.current_page_title = ""
        self.current_page_html = ""
        self.elements = {}

    async def start(self) -> BrowserResult:
        """Start mock browser."""
        self.is_started = True
        return BrowserResult(
            success=True,
            action="start",
            message="Mock browser started",
        )

    async def stop(self) -> BrowserResult:
        """Stop mock browser."""
        self.is_started = False
        return BrowserResult(
            success=True,
            action="stop",
            message="Mock browser stopped",
        )

    async def goto(self, url: str) -> BrowserResult:
        """Navigate to URL (mock)."""
        if not self.is_started:
            return BrowserResult(
                success=False,
                action="goto",
                message="Browser not started",
            )

        self.current_page_url = url
        self.current_page_title = f"Mock Page: {url}"
        self.current_page_html = f"<html><body><h1>{url}</h1></body></html>"

        return BrowserResult(
            success=True,
            action="goto",
            message=f"Navigated to {url}",
            metadata={"url": url},
        )

    async def current_url(self) -> str:
        """Get current URL."""
        return self.current_page_url

    async def get_title(self) -> str:
        """Get page title."""
        return self.current_page_title

    async def get_html(self) -> str:
        """Get page HTML."""
        return self.current_page_html

    async def get_page(self) -> BrowserPage:
        """Get current page object."""
        return BrowserPage(
            url=self.current_page_url,
            title=self.current_page_title,
            html=self.current_page_html,
        )

    async def find_element(self, selector: str) -> Optional[BrowserElement]:
        """Find element (mock)."""
        if selector in self.elements:
            return self.elements[selector]

        # Create mock element on demand
        element = BrowserElement(
            selector=selector,
            text=f"Mock element: {selector}",
            attributes={"id": selector},
            visible=True,
        )
        self.elements[selector] = element
        return element

    async def find_elements(self, selector: str) -> List[BrowserElement]:
        """Find multiple elements (mock)."""
        element = await self.find_element(selector)
        return [element] if element else []

    async def wait_for_element(self, selector: str, timeout: int = 30) -> Optional[BrowserElement]:
        """Wait for element (mock - always succeeds)."""
        return await self.find_element(selector)

    async def screenshot(self, path: str) -> BrowserResult:
        """Take screenshot (mock)."""
        return BrowserResult(
            success=True,
            action="screenshot",
            message=f"Screenshot saved to {path}",
            metadata={"path": path},
        )

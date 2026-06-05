"""
Browser Abstraction Layer

Provides implementation-independent browser interface.
Sits between ExecutionEngine and browser implementations (Playwright, Selenium, etc).

Components:
- BrowserAdapter: Abstract interface
- BrowserPage: Loaded page representation
- BrowserElement: DOM element representation
- BrowserResult: Operation result
- MockBrowserAdapter: Complete mock implementation for testing
"""

from backend.browser.adapter import BrowserAdapter, MockBrowserAdapter
from backend.browser.page import BrowserPage
from backend.browser.element import BrowserElement
from backend.browser.result import BrowserResult

__all__ = [
    "BrowserAdapter",
    "MockBrowserAdapter",
    "BrowserPage",
    "BrowserElement",
    "BrowserResult",
]

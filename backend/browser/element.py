"""
Browser Element

Represents a DOM element.
Provides mock methods for element interaction.
"""

from typing import Dict, Any, Optional
from backend.browser.result import BrowserResult


class BrowserElement:
    """Represents a DOM element."""

    def __init__(
        self,
        selector: str,
        text: str = "",
        attributes: Optional[Dict[str, str]] = None,
        visible: bool = True,
    ):
        """
        Initialize element.

        Args:
            selector: CSS selector
            text: Element text content
            attributes: Element attributes (id, name, type, etc)
            visible: Whether element is visible
        """
        self.selector = selector
        self.text = text
        self.attributes = attributes or {}
        self.visible = visible

    def click(self) -> BrowserResult:
        """
        Click the element (mock implementation).

        Returns:
            BrowserResult indicating success or failure
        """
        if not self.visible:
            return BrowserResult(
                success=False,
                action="click",
                selector=self.selector,
                message="Element not visible",
            )

        return BrowserResult(
            success=True,
            action="click",
            selector=self.selector,
            message=f"Clicked {self.selector}",
            metadata={"text": self.text},
        )

    def fill(self, value: str) -> BrowserResult:
        """
        Fill the element with value (mock implementation).

        Args:
            value: Value to fill

        Returns:
            BrowserResult indicating success or failure
        """
        if not self.visible:
            return BrowserResult(
                success=False,
                action="fill",
                selector=self.selector,
                message="Element not visible",
            )

        # Store value in metadata (simulating form fill)
        self.attributes["value"] = value

        return BrowserResult(
            success=True,
            action="fill",
            selector=self.selector,
            message=f"Filled {self.selector} with value",
            metadata={"value": value},
        )

    def get_text(self) -> str:
        """Get element text."""
        return self.text

    def get_attribute(self, name: str) -> Optional[str]:
        """Get element attribute."""
        return self.attributes.get(name)

    def __repr__(self) -> str:
        """String representation."""
        return f"BrowserElement(selector={self.selector}, text={self.text})"

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

    async def click(self) -> BrowserResult:
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

    async def fill(self, value: str) -> BrowserResult:
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

    async def get_text(self) -> str:
        """Get element text."""
        return self.text

    async def get_attribute(self, name: str) -> Optional[str]:
        """Get element attribute."""
        return self.attributes.get(name)

    async def input_value(self) -> str:
        """Get current input element value."""
        return self.attributes.get("value", "")

    async def select_option(self, value: str) -> BrowserResult:
        """Select option in a <select> element (mock implementation)."""
        if not self.visible:
            return BrowserResult(
                success=False,
                action="select_option",
                selector=self.selector,
                message="Element not visible",
            )

        self.attributes["value"] = value
        return BrowserResult(
            success=True,
            action="select_option",
            selector=self.selector,
            message=f"Selected option: {value}",
            metadata={"value": value},
        )

    async def check(self) -> BrowserResult:
        """Check a checkbox (mock implementation)."""
        if not self.visible:
            return BrowserResult(
                success=False,
                action="check",
                selector=self.selector,
                message="Element not visible",
            )

        self.attributes["checked"] = "true"
        return BrowserResult(
            success=True,
            action="check",
            selector=self.selector,
            message=f"Checked {self.selector}",
        )

    async def uncheck(self) -> BrowserResult:
        """Uncheck a checkbox (mock implementation)."""
        if not self.visible:
            return BrowserResult(
                success=False,
                action="uncheck",
                selector=self.selector,
                message="Element not visible",
            )

        self.attributes.pop("checked", None)
        return BrowserResult(
            success=True,
            action="uncheck",
            selector=self.selector,
            message=f"Unchecked {self.selector}",
        )

    async def select_radio(self, value: str) -> BrowserResult:
        """Select a radio button (mock implementation)."""
        if not self.visible:
            return BrowserResult(
                success=False,
                action="select_radio",
                selector=self.selector,
                message="Element not visible",
            )

        self.attributes["value"] = value
        self.attributes["checked"] = "true"
        return BrowserResult(
            success=True,
            action="select_radio",
            selector=self.selector,
            message=f"Selected radio: {value}",
            metadata={"value": value},
        )

    async def upload_file(self, file_path: str) -> BrowserResult:
        """
        Upload file to element (mock implementation).

        Args:
            file_path: Path to file to upload

        Returns:
            BrowserResult indicating success or failure
        """
        if not self.visible:
            return BrowserResult(
                success=False,
                action="upload_file",
                selector=self.selector,
                message="Element not visible",
            )

        # Store file path in metadata (simulating file upload)
        self.attributes["file_path"] = file_path

        return BrowserResult(
            success=True,
            action="upload_file",
            selector=self.selector,
            message=f"Uploaded file to {self.selector}",
            metadata={"file_path": file_path},
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"BrowserElement(selector={self.selector}, text={self.text})"

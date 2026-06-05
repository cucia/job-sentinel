"""
Browser Page

Represents a loaded page in the browser.
Contains page-level data and metadata.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class BrowserPage:
    """Represents a loaded page."""

    def __init__(
        self,
        url: str,
        title: str = "",
        html: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize page.

        Args:
            url: Page URL
            title: Page title
            html: Page HTML content
            metadata: Additional page metadata
        """
        self.url = url
        self.title = title
        self.html = html
        self.metadata = metadata or {}
        self.loaded_at = datetime.utcnow()

    def refresh(self):
        """Refresh the page (mock implementation)."""
        self.loaded_at = datetime.utcnow()
        return self

    def extract_html(self) -> str:
        """Extract page HTML."""
        return self.html

    def extract_metadata(self) -> Dict[str, Any]:
        """Extract page metadata."""
        return {
            "url": self.url,
            "title": self.title,
            "loaded_at": self.loaded_at.isoformat(),
            "html_length": len(self.html),
            **self.metadata,
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"BrowserPage(url={self.url}, title={self.title})"

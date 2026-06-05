"""
Browser Result

Represents the outcome of a browser operation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class BrowserResult:
    """Result of a browser operation."""

    success: bool
    """Whether the operation succeeded"""

    action: str
    """Action performed (goto, click, fill, screenshot, etc)"""

    selector: Optional[str] = None
    """CSS selector used, if applicable"""

    message: str = ""
    """Result message or error description"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional operation metadata"""

    def __repr__(self) -> str:
        """String representation."""
        status = "✓" if self.success else "✗"
        return f"{status} {self.action}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "action": self.action,
            "selector": self.selector,
            "message": self.message,
            "metadata": self.metadata,
        }

"""
Recovery Strategies

Implementations of various recovery strategies for automation failures.
"""

from enum import Enum
from typing import Optional, List
import asyncio
import logging

logger = logging.getLogger(__name__)


class RecoveryStrategy(str, Enum):
    """Available recovery strategies."""
    ALTERNATIVE_SELECTOR = "alternative_selector"
    LABEL_BASED_RECOVERY = "label_based_recovery"
    ATTRIBUTE_RECOVERY = "attribute_recovery"
    TEXT_SEARCH_RECOVERY = "text_search_recovery"
    WAIT_AND_RETRY = "wait_and_retry"
    PAGE_RESCAN = "page_rescan"


class RecoveryStrategyRegistry:
    """Registry of recovery strategies and fallback selectors."""

    # Fallback selectors for common elements
    FALLBACK_SELECTORS = {
        "submit": [
            "button[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send')",
            "input[type='submit']",
        ],
        "continue": [
            "button:has-text('Continue')",
            "button:has-text('Next')",
            "button:has-text('Proceed')",
            "a:has-text('Continue')",
        ],
        "next": [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "a:has-text('Next')",
        ],
        "apply": [
            "button:has-text('Apply')",
            "button:has-text('Submit')",
            "input[type='submit']:has-text('Apply')",
        ],
    }

    # Attribute selectors for input recovery
    INPUT_ATTRIBUTES = ["id", "name", "placeholder", "aria-label", "data-testid"]

    @classmethod
    def get_fallback_selectors(cls, original_selector: str) -> List[str]:
        """
        Get fallback selectors for a given original selector.

        Args:
            original_selector: The original CSS selector

        Returns:
            List of fallback selectors to try
        """
        fallbacks = []

        # Check if selector matches known patterns
        for pattern, alternatives in cls.FALLBACK_SELECTORS.items():
            if pattern.lower() in original_selector.lower():
                fallbacks.extend(alternatives)

        return fallbacks

    @classmethod
    def get_attribute_selectors(cls, element_id: str) -> List[str]:
        """
        Generate attribute-based selectors for an element.

        Args:
            element_id: The element ID or name

        Returns:
            List of attribute-based selectors
        """
        selectors = []

        # Try common attributes
        for attr in cls.INPUT_ATTRIBUTES:
            selectors.append(f"[{attr}='{element_id}']")
            selectors.append(f"input[{attr}='{element_id}']")
            selectors.append(f"button[{attr}='{element_id}']")

        return selectors

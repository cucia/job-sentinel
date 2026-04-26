"""
Human-like Behavior Module

Adds natural delays, typing simulation, and rate limiting to browser automation
to make the bot behavior appear more human-like.
"""

import asyncio
import random
from typing import Optional


class HumanBehavior:
    """Simulates human-like behavior in browser automation."""

    def __init__(self, settings: dict):
        self.settings = settings
        self.applications_this_session = 0
        self.max_applications_per_session = settings.get("app", {}).get("max_applications_per_session", 20)
        self.min_delay_between_actions = settings.get("app", {}).get("min_delay_ms", 500) / 1000
        self.max_delay_between_actions = settings.get("app", {}).get("max_delay_ms", 2000) / 1000

    async def random_delay(self, min_ms: Optional[int] = None, max_ms: Optional[int] = None):
        """
        Add a random delay between actions.

        Args:
            min_ms: Minimum delay in milliseconds (default: from settings)
            max_ms: Maximum delay in milliseconds (default: from settings)
        """
        min_delay = (min_ms / 1000) if min_ms else self.min_delay_between_actions
        max_delay = (max_ms / 1000) if max_ms else self.max_delay_between_actions

        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    async def type_like_human(self, element, text: str):
        """
        Type text with human-like delays between keystrokes.

        Args:
            element: Playwright element to type into
            text: Text to type
        """
        # Clear existing content first
        await element.click()
        await element.fill("")

        # Type with random delays
        for char in text:
            await element.type(char, delay=random.randint(50, 150))

    async def scroll_randomly(self, page):
        """
        Scroll the page randomly to simulate reading.

        Args:
            page: Playwright page object
        """
        try:
            # Scroll down a bit
            scroll_amount = random.randint(100, 500)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await self.random_delay(500, 1500)

            # Sometimes scroll back up
            if random.random() < 0.3:
                scroll_back = random.randint(50, 200)
                await page.evaluate(f"window.scrollBy(0, -{scroll_back})")
                await self.random_delay(300, 800)
        except Exception:
            pass

    async def move_mouse_randomly(self, page):
        """
        Move mouse to random positions to simulate human movement.

        Args:
            page: Playwright page object
        """
        try:
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y)
            await self.random_delay(100, 300)
        except Exception:
            pass

    async def click_with_delay(self, element):
        """
        Click element with human-like delay before and after.

        Args:
            element: Playwright element to click
        """
        await self.random_delay(300, 800)
        await element.click()
        await self.random_delay(500, 1200)

    async def fill_field_naturally(self, element, value: str, field_type: str = "text"):
        """
        Fill a form field with natural behavior.

        Args:
            element: Playwright element
            value: Value to fill
            field_type: Type of field (text, email, etc.)
        """
        # Click to focus
        await element.click()
        await self.random_delay(200, 500)

        # Type naturally for text fields
        if field_type in ["text", "email", "tel"]:
            await self.type_like_human(element, value)
        else:
            # For other types, use regular fill
            await element.fill(value)

        await self.random_delay(300, 700)

    def can_apply_more(self) -> bool:
        """
        Check if we can apply to more jobs in this session.

        Returns:
            True if under session limit
        """
        return self.applications_this_session < self.max_applications_per_session

    def increment_application_count(self):
        """Increment the application counter for this session."""
        self.applications_this_session += 1

    def get_session_stats(self) -> dict:
        """
        Get current session statistics.

        Returns:
            Dict with session stats
        """
        return {
            "applications_this_session": self.applications_this_session,
            "max_applications_per_session": self.max_applications_per_session,
            "remaining": self.max_applications_per_session - self.applications_this_session,
        }

    async def pause_between_applications(self):
        """
        Add a longer pause between job applications.
        """
        # Random pause between 5-15 seconds
        pause_duration = random.uniform(5, 15)
        await asyncio.sleep(pause_duration)

    async def simulate_reading(self, page, duration_ms: Optional[int] = None):
        """
        Simulate reading the page by scrolling and pausing.

        Args:
            page: Playwright page object
            duration_ms: Total duration to simulate reading (default: random 2-5s)
        """
        if duration_ms is None:
            duration_ms = random.randint(2000, 5000)

        elapsed = 0
        while elapsed < duration_ms:
            # Scroll a bit
            await self.scroll_randomly(page)
            elapsed += random.randint(500, 1500)

            # Occasionally move mouse
            if random.random() < 0.3:
                await self.move_mouse_randomly(page)

    async def wait_for_page_interaction(self, page):
        """
        Wait as if user is reading/interacting with the page.

        Args:
            page: Playwright page object
        """
        # Random wait between 1-3 seconds
        await self.random_delay(1000, 3000)

        # Sometimes scroll
        if random.random() < 0.5:
            await self.scroll_randomly(page)


def create_human_behavior(settings: dict) -> HumanBehavior:
    """
    Factory function to create HumanBehavior instance.

    Args:
        settings: Application settings

    Returns:
        HumanBehavior instance
    """
    return HumanBehavior(settings)


# Default delays for different actions (in milliseconds)
DELAYS = {
    "page_load": (1000, 3000),
    "form_field": (300, 800),
    "button_click": (500, 1200),
    "typing_per_char": (50, 150),
    "between_applications": (5000, 15000),
    "reading_page": (2000, 5000),
}


async def add_human_delay(action_type: str = "default"):
    """
    Add a human-like delay for a specific action type.

    Args:
        action_type: Type of action (page_load, form_field, button_click, etc.)
    """
    if action_type in DELAYS:
        min_ms, max_ms = DELAYS[action_type]
    else:
        min_ms, max_ms = 500, 1500

    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    await asyncio.sleep(delay)

"""
Recovery Engine

Handles recovery from automation failures using various strategies.
Integrated into ActionExecutor without creating parallel execution paths.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from backend.recovery.recovery_result import RecoveryResult
from backend.recovery.recovery_strategy import RecoveryStrategy, RecoveryStrategyRegistry

logger = logging.getLogger(__name__)


class RecoveryEngine:
    """Recovery engine for handling automation failures."""

    def __init__(self, adapter, max_retries: int = 3, wait_time: float = 1.0):
        """
        Initialize recovery engine.

        Args:
            adapter: PlaywrightAdapter instance
            max_retries: Maximum retry attempts
            wait_time: Initial wait time in seconds (exponential backoff)
        """
        self.adapter = adapter
        self.max_retries = max_retries
        self.wait_time = wait_time

    async def recover(self, original_selector: str, operation: str = "find") -> RecoveryResult:
        """
        Attempt to recover from a failed element lookup.

        Args:
            original_selector: Original selector that failed
            operation: Operation that failed (find, click, fill, etc.)

        Returns:
            RecoveryResult with recovery outcome
        """
        start_time = datetime.utcnow()
        attempts = 0

        logger.info(f"[RecoveryEngine] Starting recovery for selector: {original_selector}")

        # Strategy 1: Try fallback selectors
        logger.info(f"[RecoveryEngine] Trying alternative selectors...")
        result = await self._try_alternative_selectors(original_selector)
        if result.success:
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            return result

        # Strategy 2: Try label-based recovery (for inputs)
        logger.info(f"[RecoveryEngine] Trying label-based recovery...")
        result = await self._try_label_based_recovery(original_selector)
        if result.success:
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            return result

        # Strategy 3: Try attribute recovery
        logger.info(f"[RecoveryEngine] Trying attribute-based recovery...")
        result = await self._try_attribute_recovery(original_selector)
        if result.success:
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            return result

        # Strategy 4: Try text-based recovery (for buttons)
        logger.info(f"[RecoveryEngine] Trying text-based recovery...")
        result = await self._try_text_search_recovery(original_selector)
        if result.success:
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            return result

        # Strategy 5: Wait and retry
        logger.info(f"[RecoveryEngine] Trying wait and retry...")
        result = await self._try_wait_and_retry(original_selector)
        if result.success:
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            return result

        # Strategy 6: Page rescan
        logger.info(f"[RecoveryEngine] Trying page rescan...")
        result = await self._try_page_rescan(original_selector)
        if result.success:
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            return result

        # All strategies failed
        result = RecoveryResult(
            success=False,
            error=f"All recovery strategies exhausted for selector: {original_selector}",
        )
        result.execution_time = (datetime.utcnow() - start_time).total_seconds()
        return result

    async def _try_alternative_selectors(self, original_selector: str) -> RecoveryResult:
        """Try alternative selectors based on pattern matching."""
        fallbacks = RecoveryStrategyRegistry.get_fallback_selectors(original_selector)

        for selector in fallbacks:
            try:
                element = await self.adapter.find_element(selector)
                if element:
                    logger.info(f"[RecoveryEngine] Found element with fallback selector: {selector}")
                    return RecoveryResult(
                        success=True,
                        strategy_used=RecoveryStrategy.ALTERNATIVE_SELECTOR,
                        recovered_selector=selector,
                        metadata={"original": original_selector},
                    )
            except Exception as e:
                logger.debug(f"[RecoveryEngine] Fallback selector failed: {selector}: {e}")
                continue

        return RecoveryResult(
            success=False,
            error="No alternative selectors found",
        )

    async def _try_label_based_recovery(self, original_selector: str) -> RecoveryResult:
        """Try finding element by associated label."""
        try:
            # Extract possible field names from selector
            field_names = self._extract_field_names(original_selector)

            for field_name in field_names:
                # Try to find label with matching text
                label_selector = f"label:has-text('{field_name}')"
                label_element = await self.adapter.find_element(label_selector)

                if label_element:
                    # Get associated input
                    label_for = await label_element.get_attribute("for")
                    if label_for:
                        input_selector = f"#{label_for}"
                        element = await self.adapter.find_element(input_selector)
                        if element:
                            logger.info(f"[RecoveryEngine] Found element via label: {input_selector}")
                            return RecoveryResult(
                                success=True,
                                strategy_used=RecoveryStrategy.LABEL_BASED_RECOVERY,
                                recovered_selector=input_selector,
                                metadata={"label": field_name},
                            )
        except Exception as e:
            logger.debug(f"[RecoveryEngine] Label-based recovery failed: {e}")

        return RecoveryResult(success=False, error="Label-based recovery failed")

    async def _try_attribute_recovery(self, original_selector: str) -> RecoveryResult:
        """Try finding element by attributes."""
        try:
            field_names = self._extract_field_names(original_selector)

            for field_name in field_names:
                selectors = RecoveryStrategyRegistry.get_attribute_selectors(field_name)

                for selector in selectors:
                    try:
                        element = await self.adapter.find_element(selector)
                        if element:
                            logger.info(f"[RecoveryEngine] Found element via attributes: {selector}")
                            return RecoveryResult(
                                success=True,
                                strategy_used=RecoveryStrategy.ATTRIBUTE_RECOVERY,
                                recovered_selector=selector,
                                metadata={"field_name": field_name},
                            )
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"[RecoveryEngine] Attribute recovery failed: {e}")

        return RecoveryResult(success=False, error="Attribute recovery failed")

    async def _try_text_search_recovery(self, original_selector: str) -> RecoveryResult:
        """Try finding buttons/elements by visible text."""
        try:
            # Extract text from selector if possible
            text_patterns = [
                "submit", "apply", "continue", "next",
                "send", "confirm", "ok", "yes"
            ]

            for pattern in text_patterns:
                if pattern.lower() in original_selector.lower():
                    selector = f"button:has-text('{pattern.capitalize()}')"
                    element = await self.adapter.find_element(selector)
                    if element:
                        logger.info(f"[RecoveryEngine] Found element via text: {selector}")
                        return RecoveryResult(
                            success=True,
                            strategy_used=RecoveryStrategy.TEXT_SEARCH_RECOVERY,
                            recovered_selector=selector,
                            metadata={"pattern": pattern},
                        )
        except Exception as e:
            logger.debug(f"[RecoveryEngine] Text search recovery failed: {e}")

        return RecoveryResult(success=False, error="Text search recovery failed")

    async def _try_wait_and_retry(self, original_selector: str) -> RecoveryResult:
        """Retry with exponential backoff."""
        wait_time = self.wait_time

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"[RecoveryEngine] Retry attempt {attempt + 1}/{self.max_retries}, "
                    f"waiting {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

                element = await self.adapter.find_element(original_selector)
                if element:
                    logger.info(
                        f"[RecoveryEngine] Element found after retry "
                        f"(attempt {attempt + 1})"
                    )
                    return RecoveryResult(
                        success=True,
                        strategy_used=RecoveryStrategy.WAIT_AND_RETRY,
                        attempts=attempt + 1,
                        recovered_selector=original_selector,
                    )

                wait_time *= 2  # Exponential backoff
            except Exception as e:
                logger.debug(f"[RecoveryEngine] Retry {attempt + 1} failed: {e}")
                wait_time *= 2

        return RecoveryResult(
            success=False,
            error=f"Element not found after {self.max_retries} retries",
            attempts=self.max_retries,
        )

    async def _try_page_rescan(self, original_selector: str) -> RecoveryResult:
        """Rescan page DOM and retry."""
        try:
            logger.info("[RecoveryEngine] Rescanning page DOM...")

            # Wait for page to stabilize
            await asyncio.sleep(2)

            # Try to find element again
            element = await self.adapter.find_element(original_selector)
            if element:
                logger.info("[RecoveryEngine] Element found after page rescan")
                return RecoveryResult(
                    success=True,
                    strategy_used=RecoveryStrategy.PAGE_RESCAN,
                    recovered_selector=original_selector,
                )
        except Exception as e:
            logger.debug(f"[RecoveryEngine] Page rescan failed: {e}")

        return RecoveryResult(success=False, error="Page rescan failed")

    def _extract_field_names(self, selector: str) -> list:
        """Extract possible field names from selector."""
        names = []

        # Extract from ID
        if "#" in selector:
            id_part = selector.split("#")[1].split("]")[0].split("[")[0].split(":")[0]
            names.append(id_part)

        # Extract from name attribute
        if "name=" in selector:
            name_part = selector.split("name=")[1].split("]")[0].strip("'\"")
            names.append(name_part)

        return names

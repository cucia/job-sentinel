"""
Submission Verification Module

Verifies successful job application submissions by checking:
- Success messages and confirmation text
- Redirect URLs (thank you pages, confirmation pages)
- Error alerts and validation messages
- Page state changes
"""

from typing import Dict, Optional, Tuple
from src.core.logger import log


class SubmissionVerifier:
    """Verifies job application submission success."""

    # Success indicators
    SUCCESS_MESSAGES = [
        "application submitted",
        "thank you for applying",
        "successfully submitted",
        "application received",
        "we've received your application",
        "your application has been submitted",
        "application complete",
        "thanks for your interest",
        "we'll be in touch",
        "application sent",
    ]

    # Success URL patterns
    SUCCESS_URL_PATTERNS = [
        "/confirmation",
        "/thank-you",
        "/success",
        "/application-complete",
        "/submitted",
        "/applied",
    ]

    # Error indicators
    ERROR_MESSAGES = [
        "error",
        "failed",
        "invalid",
        "required field",
        "please fill",
        "missing information",
        "something went wrong",
        "try again",
        "unable to submit",
        "submission failed",
    ]

    async def verify_submission(self, page, task_context) -> Dict[str, any]:
        """
        Verify if application submission was successful.

        Args:
            page: Playwright page object
            task_context: TaskContext object

        Returns:
            {
                "status": "success" | "failed" | "uncertain",
                "confidence": 0-100,
                "evidence": [str],
                "error_messages": [str]
            }
        """
        evidence = []
        error_messages = []
        confidence = 0

        try:
            # Wait for page to settle
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        # Check 1: Success messages in page content
        success_msg_found = await self._check_success_messages(page)
        if success_msg_found:
            evidence.append(f"Success message: {success_msg_found}")
            confidence += 40

        # Check 2: URL changed to success page
        current_url = page.url.lower()
        url_indicates_success = any(pattern in current_url for pattern in self.SUCCESS_URL_PATTERNS)
        if url_indicates_success:
            evidence.append(f"Success URL pattern: {current_url}")
            confidence += 30

        # Check 3: Error messages present
        error_msg_found = await self._check_error_messages(page)
        if error_msg_found:
            error_messages.extend(error_msg_found)
            confidence -= 50

        # Check 4: Form still visible (indicates failure)
        form_still_present = await self._check_form_present(page)
        if form_still_present and not success_msg_found:
            evidence.append("Form still present (possible failure)")
            confidence -= 20

        # Check 5: Success modal or overlay
        modal_found = await self._check_success_modal(page)
        if modal_found:
            evidence.append("Success modal detected")
            confidence += 25

        # Determine final status
        if confidence >= 50:
            status = "success"
        elif confidence <= -20 or error_messages:
            status = "failed"
        else:
            status = "uncertain"

        log(f"[Verification] Status: {status}, Confidence: {confidence}, Evidence: {evidence}")

        return {
            "status": status,
            "confidence": max(0, min(100, confidence)),
            "evidence": evidence,
            "error_messages": error_messages,
        }

    async def _check_success_messages(self, page) -> Optional[str]:
        """Check for success messages in page content."""
        try:
            page_text = await page.text_content("body")
            if not page_text:
                return None

            page_text_lower = page_text.lower()
            for msg in self.SUCCESS_MESSAGES:
                if msg in page_text_lower:
                    return msg
            return None
        except Exception:
            return None

    async def _check_error_messages(self, page) -> list[str]:
        """Check for error messages on the page."""
        errors = []
        try:
            # Check for common error selectors
            error_selectors = [
                ".error",
                ".error-message",
                ".alert-error",
                ".alert-danger",
                "[role='alert']",
                ".validation-error",
                ".field-error",
            ]

            for selector in error_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    is_visible = await element.is_visible()
                    if is_visible:
                        text = await element.text_content()
                        if text and text.strip():
                            errors.append(text.strip())

            # Also check page text for error keywords
            if not errors:
                page_text = await page.text_content("body")
                if page_text:
                    page_text_lower = page_text.lower()
                    for error_msg in self.ERROR_MESSAGES:
                        if error_msg in page_text_lower:
                            errors.append(error_msg)
                            break

        except Exception:
            pass

        return errors[:5]  # Limit to 5 errors

    async def _check_form_present(self, page) -> bool:
        """Check if application form is still present."""
        try:
            forms = await page.query_selector_all("form")
            for form in forms:
                is_visible = await form.is_visible()
                if is_visible:
                    return True
            return False
        except Exception:
            return False

    async def _check_success_modal(self, page) -> bool:
        """Check for success modal or overlay."""
        try:
            modal_selectors = [
                ".modal:has-text('success')",
                ".modal:has-text('submitted')",
                ".modal:has-text('thank you')",
                "[role='dialog']:has-text('success')",
                "[role='dialog']:has-text('submitted')",
            ]

            for selector in modal_selectors:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        return True
            return False
        except Exception:
            return False

    async def verify_with_screenshot(self, page, task_context, screenshot_path: Optional[str] = None) -> Dict[str, any]:
        """
        Verify submission and optionally capture screenshot for uncertain cases.

        Args:
            page: Playwright page object
            task_context: TaskContext object
            screenshot_path: Optional path to save screenshot

        Returns:
            Verification result dict
        """
        result = await self.verify_submission(page, task_context)

        # Capture screenshot for uncertain or failed cases
        if result["status"] in ["uncertain", "failed"] and screenshot_path:
            try:
                await page.screenshot(path=screenshot_path, full_page=True)
                result["screenshot"] = screenshot_path
                log(f"[Verification] Screenshot saved: {screenshot_path}")
            except Exception as exc:
                log(f"[Verification] Screenshot failed: {exc}")

        return result


async def verify_submission(page, task_context) -> Dict[str, any]:
    """
    Convenience function to verify submission.

    Args:
        page: Playwright page object
        task_context: TaskContext object

    Returns:
        Verification result dict
    """
    verifier = SubmissionVerifier()
    return await verifier.verify_submission(page, task_context)

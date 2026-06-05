"""
LinkedIn Detector

Detects LinkedIn pages and determines page type.
Works with DOM content and URLs.
"""

import logging
from typing import Optional

from backend.platforms.linkedin.linkedin_page_data import LinkedInPageType

logger = logging.getLogger(__name__)


class LinkedInDetector:
    """Detects LinkedIn pages and page types."""

    # LinkedIn URL patterns
    LINKEDIN_DOMAINS = [
        "linkedin.com",
        "www.linkedin.com",
    ]

    # Page type indicators
    EASY_APPLY_INDICATORS = [
        "Easy Apply",
        "easy-apply",
        "easyApply",
        "Apply now",
    ]

    EXTERNAL_APPLY_INDICATORS = [
        "Apply on company website",
        "Go to company website",
        "external-apply",
        "externalApply",
    ]

    JOB_PAGE_INDICATORS = [
        "job-details",
        "jobs/view",
        "jobs/search",
        "linkedin.com/jobs/view",
    ]

    def __init__(self, adapter=None):
        """
        Initialize detector.

        Args:
            adapter: PlaywrightAdapter instance (optional)
        """
        self.adapter = adapter

    async def is_linkedin_page(self, url: str, page_title: Optional[str] = None) -> bool:
        """
        Check if current page is a LinkedIn page.

        Args:
            url: Current page URL
            page_title: Page title (optional)

        Returns:
            True if LinkedIn page
        """
        if not url:
            return False

        # Check domain
        for domain in self.LINKEDIN_DOMAINS:
            if domain in url.lower():
                return True

        # Check page title (LinkedIn jobs have specific format)
        if page_title:
            if "linkedin" in page_title.lower() and "job" in page_title.lower():
                return True

        # Mock pages with LinkedIn Jobs in title
        if page_title and "linkedin" in page_title.lower() and "job" in page_title.lower():
            return True

        return False

    async def is_job_page(self, url: str, html: Optional[str] = None) -> bool:
        """
        Check if page is a LinkedIn job page.

        Args:
            url: Current page URL
            html: Page HTML (optional)

        Returns:
            True if job page
        """
        if not await self.is_linkedin_page(url):
            return False

        # Check URL patterns
        for indicator in self.JOB_PAGE_INDICATORS:
            if indicator in url.lower():
                return True

        # Check HTML if provided
        if html:
            for indicator in self.JOB_PAGE_INDICATORS:
                if indicator.lower() in html.lower():
                    return True

        return False

    async def is_easy_apply(self, html: Optional[str] = None) -> bool:
        """
        Check if page has Easy Apply button.

        Args:
            html: Page HTML

        Returns:
            True if Easy Apply available
        """
        if not html:
            if self.adapter:
                try:
                    page = await self.adapter.get_page()
                    html = await page.content()
                except Exception as e:
                    logger.warning(f"Failed to get page content: {e}")
                    return False
            else:
                return False

        for indicator in self.EASY_APPLY_INDICATORS:
            if indicator.lower() in html.lower():
                return True

        return False

    async def is_external_apply(self, html: Optional[str] = None) -> bool:
        """
        Check if page has external apply option.

        Args:
            html: Page HTML

        Returns:
            True if external apply available
        """
        if not html:
            if self.adapter:
                try:
                    page = await self.adapter.get_page()
                    html = await page.content()
                except Exception as e:
                    logger.warning(f"Failed to get page content: {e}")
                    return False
            else:
                return False

        for indicator in self.EXTERNAL_APPLY_INDICATORS:
            if indicator.lower() in html.lower():
                return True

        return False

    async def get_page_type(self, url: str, html: Optional[str] = None) -> LinkedInPageType:
        """
        Determine LinkedIn page type.

        Args:
            url: Current page URL
            html: Page HTML (optional)

        Returns:
            LinkedInPageType
        """
        # Check if LinkedIn page
        if not await self.is_linkedin_page(url):
            return LinkedInPageType.UNKNOWN

        # Check if job page
        if not await self.is_job_page(url, html):
            if "jobs/search" in url.lower():
                return LinkedInPageType.SEARCH_RESULTS
            return LinkedInPageType.UNKNOWN

        # Check apply methods
        has_easy_apply = await self.is_easy_apply(html)
        has_external_apply = await self.is_external_apply(html)

        if has_easy_apply and not has_external_apply:
            return LinkedInPageType.EASY_APPLY_PAGE
        elif has_external_apply and not has_easy_apply:
            return LinkedInPageType.EXTERNAL_APPLY_PAGE
        elif has_easy_apply and has_external_apply:
            return LinkedInPageType.EASY_APPLY_PAGE  # Prefer Easy Apply

        return LinkedInPageType.JOB_PAGE

    def extract_job_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract job ID from LinkedIn URL.

        Args:
            url: LinkedIn job URL

        Returns:
            Job ID if found
        """
        try:
            # Pattern: jobs/view/123456789/
            if "/jobs/view/" in url:
                parts = url.split("/jobs/view/")
                if len(parts) > 1:
                    job_id = parts[1].split("/")[0]
                    return job_id
        except Exception as e:
            logger.warning(f"Failed to extract job ID: {e}")

        return None

"""
LinkedIn Job Parser

Extracts job metadata from LinkedIn job pages.
Works with DOM selectors and HTML parsing.
"""

import logging
import re
from typing import Optional

from backend.platforms.linkedin.linkedin_page_data import LinkedInPageData, LinkedInPageType

logger = logging.getLogger(__name__)


class LinkedInJobParser:
    """Parses LinkedIn job page metadata."""

    def __init__(self, adapter=None, workflow_classifier=None):
        """
        Initialize parser.

        Args:
            adapter: PlaywrightAdapter instance (optional)
            workflow_classifier: LinkedInWorkflowClassifier instance (optional)
        """
        self.adapter = adapter
        self.workflow_classifier = workflow_classifier

    async def parse(self, url: str, html: Optional[str] = None) -> LinkedInPageData:
        """
        Parse LinkedIn job page and extract metadata.

        Args:
            url: Current page URL
            html: Page HTML content (optional)

        Returns:
            LinkedInPageData with extracted information
        """
        page_data = LinkedInPageData(url=url, is_linkedin=True)

        if not html and self.adapter:
            try:
                page = await self.adapter.get_page()
                html = await page.content()
                page_data.page_title = await page.title()
            except Exception as e:
                logger.warning(f"Failed to get page content: {e}")
                return page_data

        if not html:
            return page_data

        # Extract job information
        page_data.job_title = self._extract_job_title(html)
        page_data.company_name = self._extract_company(html)
        page_data.location = self._extract_location(html)
        page_data.employment_type = self._extract_employment_type(html)
        page_data.experience_level = self._extract_experience_level(html)
        page_data.job_description = self._extract_job_description(html)

        # Check apply methods
        page_data.easy_apply_available = self._check_easy_apply(html)
        page_data.external_apply_available = self._check_external_apply(html)

        # Determine page type
        page_data.page_type = self._determine_page_type(html)

        # Classify workflow type using classifier if available
        if self.workflow_classifier:
            page_data.workflow_type = self.workflow_classifier.classify(page_data)
            logger.info(f"[Parser] Classified workflow: {page_data.workflow_type}")
        else:
            logger.warning("[Parser] No workflow classifier provided, workflow_type will be UNKNOWN")

        return page_data

    def _extract_job_title(self, html: str) -> Optional[str]:
        """Extract job title from HTML."""
        try:
            # Priority 1: H1 with job-title class
            patterns = [
                r'<h1[^>]*class="[^"]*job-title[^"]*"[^>]*>([^<]+)</h1>',
                r'<h1[^>]*>([^<]+)</h1>',
                r'<title>([^-]+)\s*-\s*LinkedIn',
                r'data-test="job-title"[^>]*>([^<]+)<',
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if title and len(title) > 3 and not title.lower().startswith('linkedin'):
                        logger.info(f"[Parser] Extracted job title: {title}")
                        return title
        except Exception as e:
            logger.warning(f"Failed to extract job title: {e}")

        return None

    def _extract_company(self, html: str) -> Optional[str]:
        """Extract company name from HTML."""
        try:
            # Priority 1: Div with company class
            patterns = [
                r'<div[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)<',
                r'data-test="job-card-company-name"[^>]*>([^<]+)<',
                r'data-test="company-name"[^>]*>([^<]+)<',
                r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)<',
                r'<a[^>]*href="/company/[^"]*"[^>]*>([^<]+)<',
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
                    if company and len(company) > 1:
                        logger.info(f"[Parser] Extracted company: {company}")
                        return company
        except Exception as e:
            logger.warning(f"Failed to extract company: {e}")

        return None

    def _extract_location(self, html: str) -> Optional[str]:
        """Extract location from HTML."""
        try:
            # Priority 1: Span with location emoji or meta section
            patterns = [
                r'<span>📍\s*([^<]+)</span>',
                r'data-test="job-details-location"[^>]*>([^<]+)<',
                r'<span[^>]*class="[^"]*location[^"]*"[^>]*>([^<]+)<',
                r'<li[^>]*class="[^"]*location[^"]*"[^>]*>([^<]+)<',
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    if location and location != '📍':
                        logger.info(f"[Parser] Extracted location: {location}")
                        return location
        except Exception as e:
            logger.warning(f"Failed to extract location: {e}")

        return None

    def _extract_employment_type(self, html: str) -> Optional[str]:
        """Extract employment type from HTML."""
        try:
            employment_types = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"]

            # Look for emoji pattern first
            for emp_type in employment_types:
                # Try with emoji pattern
                pattern = rf'💼\s*{emp_type}'
                if re.search(pattern, html, re.IGNORECASE):
                    logger.info(f"[Parser] Extracted employment type: {emp_type}")
                    return emp_type

            # Fallback to text search
            for emp_type in employment_types:
                if emp_type.lower() in html.lower():
                    logger.info(f"[Parser] Extracted employment type: {emp_type}")
                    return emp_type
        except Exception as e:
            logger.warning(f"Failed to extract employment type: {e}")

        return None

    def _extract_experience_level(self, html: str) -> Optional[str]:
        """Extract experience level from HTML."""
        try:
            experience_levels = [
                "Entry level",
                "Mid-Level",
                "Senior",
                "Executive",
                "Not Applicable",
            ]

            # Look for emoji pattern first
            for level in experience_levels:
                pattern = rf'📊\s*{level}'
                if re.search(pattern, html, re.IGNORECASE):
                    logger.info(f"[Parser] Extracted experience level: {level}")
                    return level

            # Fallback to text search
            for level in experience_levels:
                if level.lower() in html.lower():
                    logger.info(f"[Parser] Extracted experience level: {level}")
                    return level
        except Exception as e:
            logger.warning(f"Failed to extract experience level: {e}")

        return None

    def _extract_job_description(self, html: str) -> Optional[str]:
        """Extract job description from HTML."""
        try:
            # Look for description containers
            patterns = [
                r'<section[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</section>',
                r'<div[^>]*class="[^"]*show-more[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    description = match.group(1).strip()
                    # Remove HTML tags
                    description = re.sub(r'<[^>]+>', '', description).strip()
                    if description and len(description) > 50:
                        logger.info(f"[Parser] Extracted description ({len(description)} chars)")
                        return description[:500]  # Limit to 500 chars
        except Exception as e:
            logger.warning(f"Failed to extract description: {e}")

        return None

    def _check_easy_apply(self, html: str) -> bool:
        """Check if Easy Apply is available."""
        try:
            indicators = ["Easy Apply", "easy-apply", "easyApply"]
            for indicator in indicators:
                if indicator in html:
                    logger.info("[Parser] Easy Apply detected")
                    return True
        except Exception as e:
            logger.warning(f"Failed to check Easy Apply: {e}")

        return False

    def _check_external_apply(self, html: str) -> bool:
        """Check if external apply is available."""
        try:
            indicators = [
                "Apply on company website",
                "Go to company website",
                "external-apply",
            ]
            for indicator in indicators:
                if indicator.lower() in html.lower():
                    logger.info("[Parser] External apply detected")
                    return True
        except Exception as e:
            logger.warning(f"Failed to check external apply: {e}")

        return False

    def _determine_page_type(self, html: str) -> LinkedInPageType:
        """Determine page type from HTML."""
        if self._check_easy_apply(html):
            return LinkedInPageType.EASY_APPLY_PAGE
        elif self._check_external_apply(html):
            return LinkedInPageType.EXTERNAL_APPLY_PAGE
        else:
            return LinkedInPageType.JOB_PAGE

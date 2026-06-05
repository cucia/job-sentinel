"""
LinkedIn Page Data

Dataclass representing extracted LinkedIn job page information.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class LinkedInPageType(str, Enum):
    """LinkedIn page types."""
    JOB_PAGE = "job_page"
    EASY_APPLY_PAGE = "easy_apply_page"
    EXTERNAL_APPLY_PAGE = "external_apply_page"
    SEARCH_RESULTS = "search_results"
    UNKNOWN = "unknown"


class LinkedInWorkflowType(str, Enum):
    """LinkedIn workflow types."""
    EASY_APPLY = "easy_apply"
    MULTI_STEP_EASY_APPLY = "multi_step_easy_apply"
    EXTERNAL_REDIRECT = "external_redirect"
    UNKNOWN = "unknown"


@dataclass
class LinkedInPageData:
    """Extracted LinkedIn job page data."""

    # Job information
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    job_description: Optional[str] = None

    # Application methods
    easy_apply_available: bool = False
    external_apply_available: bool = False

    # Page classification
    page_type: LinkedInPageType = LinkedInPageType.UNKNOWN
    workflow_type: LinkedInWorkflowType = LinkedInWorkflowType.UNKNOWN

    # URL
    url: Optional[str] = None

    # Metadata
    is_linkedin: bool = False
    page_title: Optional[str] = None

    def __str__(self):
        """String representation."""
        lines = [
            f"LinkedIn Page Data",
            f"  Job: {self.job_title}",
            f"  Company: {self.company_name}",
            f"  Location: {self.location}",
            f"  Employment Type: {self.employment_type}",
            f"  Experience Level: {self.experience_level}",
            f"  Page Type: {self.page_type}",
            f"  Workflow Type: {self.workflow_type}",
            f"  Easy Apply: {self.easy_apply_available}",
            f"  External Apply: {self.external_apply_available}",
        ]
        return "\n".join(lines)

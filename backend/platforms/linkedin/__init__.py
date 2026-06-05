"""
LinkedIn Platform Module

LinkedIn-specific page understanding, parsing, and workflow classification.
Integrates with existing Job Sentinel architecture.
"""

from backend.platforms.linkedin.linkedin_page_data import (
    LinkedInPageData,
    LinkedInPageType,
    LinkedInWorkflowType,
)
from backend.platforms.linkedin.linkedin_detector import LinkedInDetector
from backend.platforms.linkedin.linkedin_job_parser import LinkedInJobParser
from backend.platforms.linkedin.linkedin_workflow_classifier import LinkedInWorkflowClassifier

__all__ = [
    "LinkedInPageData",
    "LinkedInPageType",
    "LinkedInWorkflowType",
    "LinkedInDetector",
    "LinkedInJobParser",
    "LinkedInWorkflowClassifier",
]

"""
LinkedIn Platform Module

LinkedIn-specific page understanding, parsing, workflow classification, and plan generation.
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
from backend.platforms.linkedin.linkedin_plan_generator import LinkedInPlanGenerator

__all__ = [
    "LinkedInPageData",
    "LinkedInPageType",
    "LinkedInWorkflowType",
    "LinkedInDetector",
    "LinkedInJobParser",
    "LinkedInWorkflowClassifier",
    "LinkedInPlanGenerator",
]

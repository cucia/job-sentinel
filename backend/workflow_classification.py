"""
Phase 2 - Workflow Classification

Identifies application workflow types and selects execution strategies.

Supported workflows:
- LinkedIn Easy Apply
- Workday
- Greenhouse
- Lever
- Oracle
- Generic/Unknown

Input: URL, page metadata, DOM information
Output: workflow_type, confidence_score, execution_strategy
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class WorkflowType(Enum):
    """Supported application workflow types."""
    LINKEDIN_EASY_APPLY = "linkedin_easy_apply"
    WORKDAY = "workday"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ORACLE = "oracle"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class ExecutionStrategy(Enum):
    """Execution strategies for different workflow types."""
    LINKEDIN_EASY_APPLY_FLOW = "linkedin_easy_apply_flow"
    WORKDAY_FLOW = "workday_flow"
    GREENHOUSE_FLOW = "greenhouse_flow"
    LEVER_FLOW = "lever_flow"
    ORACLE_FLOW = "oracle_flow"
    GENERIC_FORM_FLOW = "generic_form_flow"
    MANUAL_REVIEW = "manual_review"


@dataclass
class WorkflowClassification:
    """Result of workflow classification."""
    workflow_type: WorkflowType
    confidence_score: float  # 0.0 to 1.0
    execution_strategy: ExecutionStrategy
    indicators: dict  # Detected indicators for this workflow
    reasoning: str  # Explanation of classification


class WorkflowClassifier:
    """Classifies application workflows and selects execution strategies."""

    def __init__(self):
        """Initialize workflow classifier."""
        self.classifiers = {
            WorkflowType.LINKEDIN_EASY_APPLY: self._classify_linkedin_easy_apply,
            WorkflowType.WORKDAY: self._classify_workday,
            WorkflowType.GREENHOUSE: self._classify_greenhouse,
            WorkflowType.LEVER: self._classify_lever,
            WorkflowType.ORACLE: self._classify_oracle,
            WorkflowType.GENERIC: self._classify_generic,
        }

    def classify(
        self,
        url: str,
        page_title: Optional[str] = None,
        page_metadata: Optional[dict] = None,
        dom_info: Optional[dict] = None,
    ) -> WorkflowClassification:
        """
        Classify application workflow.

        Args:
            url: Application URL
            page_title: Page title
            page_metadata: Page metadata (og:, meta tags, etc.)
            dom_info: DOM information (selectors, classes, ids)

        Returns:
            WorkflowClassification with type, confidence, and strategy
        """
        # Normalize inputs
        page_metadata = page_metadata or {}
        dom_info = dom_info or {}

        # Run all classifiers
        results = []
        for workflow_type, classifier in self.classifiers.items():
            result = classifier(url, page_title, page_metadata, dom_info)
            if result:
                results.append(result)

        # Sort by confidence (highest first)
        results.sort(key=lambda x: x["confidence"], reverse=True)

        # Return best match or generic fallback
        if results and results[0]["confidence"] > 0.0:
            best = results[0]
            return WorkflowClassification(
                workflow_type=best["type"],
                confidence_score=best["confidence"],
                execution_strategy=best["strategy"],
                indicators=best["indicators"],
                reasoning=best["reasoning"],
            )

        return WorkflowClassification(
            workflow_type=WorkflowType.GENERIC,
            confidence_score=0.0,
            execution_strategy=ExecutionStrategy.GENERIC_FORM_FLOW,
            indicators={"fallback_to_generic": True},
            reasoning="Could not classify specifically, treating as generic form",
        )

    def _classify_linkedin_easy_apply(
        self, url: str, page_title: Optional[str], page_metadata: dict, dom_info: dict
    ) -> Optional[dict]:
        """Classify LinkedIn Easy Apply workflow."""
        indicators = {}
        confidence = 0.0

        # URL indicators
        if "linkedin.com" in url.lower():
            indicators["linkedin_url"] = True
            confidence += 0.3

        if "/jobs/" in url.lower():
            indicators["jobs_path"] = True
            confidence += 0.2

        # Page title indicators
        if page_title and "linkedin" in page_title.lower():
            indicators["linkedin_title"] = True
            confidence += 0.1

        # Metadata indicators
        if page_metadata.get("og:site_name") == "LinkedIn":
            indicators["linkedin_og_site"] = True
            confidence += 0.2

        # DOM indicators
        if dom_info.get("easy_apply_button"):
            indicators["easy_apply_button"] = True
            confidence += 0.3

        if dom_info.get("linkedin_job_card"):
            indicators["linkedin_job_card"] = True
            confidence += 0.2

        if confidence > 0.0:
            return {
                "type": WorkflowType.LINKEDIN_EASY_APPLY,
                "confidence": min(confidence, 1.0),
                "strategy": ExecutionStrategy.LINKEDIN_EASY_APPLY_FLOW,
                "indicators": indicators,
                "reasoning": f"LinkedIn Easy Apply detected with {len(indicators)} indicators",
            }

        return None

    def _classify_workday(
        self, url: str, page_title: Optional[str], page_metadata: dict, dom_info: dict
    ) -> Optional[dict]:
        """Classify Workday workflow."""
        indicators = {}
        confidence = 0.0

        # URL indicators
        if "workday.com" in url.lower():
            indicators["workday_domain"] = True
            confidence += 0.4

        if "/careers" in url.lower() or "/jobs" in url.lower():
            indicators["careers_path"] = True
            confidence += 0.2

        # Page title indicators
        if page_title and "workday" in page_title.lower():
            indicators["workday_title"] = True
            confidence += 0.2

        # Metadata indicators
        if "workday" in page_metadata.get("og:site_name", "").lower():
            indicators["workday_og_site"] = True
            confidence += 0.2

        # DOM indicators
        if dom_info.get("workday_form"):
            indicators["workday_form"] = True
            confidence += 0.3

        if dom_info.get("workday_iframe"):
            indicators["workday_iframe"] = True
            confidence += 0.2

        if confidence > 0.0:
            return {
                "type": WorkflowType.WORKDAY,
                "confidence": min(confidence, 1.0),
                "strategy": ExecutionStrategy.WORKDAY_FLOW,
                "indicators": indicators,
                "reasoning": f"Workday detected with {len(indicators)} indicators",
            }

        return None

    def _classify_greenhouse(
        self, url: str, page_title: Optional[str], page_metadata: dict, dom_info: dict
    ) -> Optional[dict]:
        """Classify Greenhouse workflow."""
        indicators = {}
        confidence = 0.0

        # URL indicators
        if "greenhouse.io" in url.lower():
            indicators["greenhouse_domain"] = True
            confidence += 0.4

        if "boards.greenhouse.io" in url.lower():
            indicators["greenhouse_boards"] = True
            confidence += 0.2

        # Page title indicators
        if page_title and "greenhouse" in page_title.lower():
            indicators["greenhouse_title"] = True
            confidence += 0.2

        # Metadata indicators
        if "greenhouse" in page_metadata.get("og:site_name", "").lower():
            indicators["greenhouse_og_site"] = True
            confidence += 0.2

        # DOM indicators
        if dom_info.get("greenhouse_form"):
            indicators["greenhouse_form"] = True
            confidence += 0.3

        if dom_info.get("greenhouse_job_board"):
            indicators["greenhouse_job_board"] = True
            confidence += 0.2

        if confidence > 0.0:
            return {
                "type": WorkflowType.GREENHOUSE,
                "confidence": min(confidence, 1.0),
                "strategy": ExecutionStrategy.GREENHOUSE_FLOW,
                "indicators": indicators,
                "reasoning": f"Greenhouse detected with {len(indicators)} indicators",
            }

        return None

    def _classify_lever(
        self, url: str, page_title: Optional[str], page_metadata: dict, dom_info: dict
    ) -> Optional[dict]:
        """Classify Lever workflow."""
        indicators = {}
        confidence = 0.0

        # URL indicators
        if "lever.co" in url.lower():
            indicators["lever_domain"] = True
            confidence += 0.4

        if "/jobs/" in url.lower():
            indicators["jobs_path"] = True
            confidence += 0.1

        # Page title indicators
        if page_title and "lever" in page_title.lower():
            indicators["lever_title"] = True
            confidence += 0.2

        # Metadata indicators
        if "lever" in page_metadata.get("og:site_name", "").lower():
            indicators["lever_og_site"] = True
            confidence += 0.2

        # DOM indicators
        if dom_info.get("lever_form"):
            indicators["lever_form"] = True
            confidence += 0.3

        if dom_info.get("lever_job_posting"):
            indicators["lever_job_posting"] = True
            confidence += 0.2

        if confidence > 0.0:
            return {
                "type": WorkflowType.LEVER,
                "confidence": min(confidence, 1.0),
                "strategy": ExecutionStrategy.LEVER_FLOW,
                "indicators": indicators,
                "reasoning": f"Lever detected with {len(indicators)} indicators",
            }

        return None

    def _classify_oracle(
        self, url: str, page_title: Optional[str], page_metadata: dict, dom_info: dict
    ) -> Optional[dict]:
        """Classify Oracle workflow."""
        indicators = {}
        confidence = 0.0

        # URL indicators
        if "oracle.com" in url.lower():
            indicators["oracle_domain"] = True
            confidence += 0.3

        if "/careers" in url.lower() or "/jobs" in url.lower():
            indicators["careers_path"] = True
            confidence += 0.1

        # Page title indicators
        if page_title and "oracle" in page_title.lower():
            indicators["oracle_title"] = True
            confidence += 0.2

        # Metadata indicators
        if "oracle" in page_metadata.get("og:site_name", "").lower():
            indicators["oracle_og_site"] = True
            confidence += 0.2

        # DOM indicators
        if dom_info.get("oracle_form"):
            indicators["oracle_form"] = True
            confidence += 0.3

        if dom_info.get("oracle_careers_portal"):
            indicators["oracle_careers_portal"] = True
            confidence += 0.2

        if confidence > 0.0:
            return {
                "type": WorkflowType.ORACLE,
                "confidence": min(confidence, 1.0),
                "strategy": ExecutionStrategy.ORACLE_FLOW,
                "indicators": indicators,
                "reasoning": f"Oracle detected with {len(indicators)} indicators",
            }

        return None

    def _classify_generic(
        self, url: str, page_title: Optional[str], page_metadata: dict, dom_info: dict
    ) -> Optional[dict]:
        """Classify Generic/Unknown workflow."""
        indicators = {}
        confidence = 0.0

        # Generic form indicators
        if dom_info.get("form_fields"):
            indicators["form_fields"] = True
            confidence += 0.2

        if dom_info.get("submit_button"):
            indicators["submit_button"] = True
            confidence += 0.2

        if dom_info.get("application_form"):
            indicators["application_form"] = True
            confidence += 0.3

        # Generic job posting indicators
        if dom_info.get("job_title"):
            indicators["job_title"] = True
            confidence += 0.1

        if dom_info.get("job_description"):
            indicators["job_description"] = True
            confidence += 0.1

        if confidence > 0.0:
            return {
                "type": WorkflowType.GENERIC,
                "confidence": min(confidence, 1.0),
                "strategy": ExecutionStrategy.GENERIC_FORM_FLOW,
                "indicators": indicators,
                "reasoning": f"Generic workflow detected with {len(indicators)} indicators",
            }

        return None


def create_classifier() -> WorkflowClassifier:
    """Factory function to create workflow classifier."""
    return WorkflowClassifier()

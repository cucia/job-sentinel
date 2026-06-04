"""
Page Analysis Component

Analyzes page structures and extracts normalized information.
Works with pre-extracted page data (not browser-dependent).

Supports:
- Page type detection
- Form extraction
- Field extraction
- Button extraction
- Navigation detection
- Validation message extraction
"""

from typing import Optional, Dict, List, Any
from backend.application.session import (
    PageAnalysisResult,
    PageForm,
    PageElement,
)
from src.core.logger import log


class PageAnalyzer:
    """Analyzes page structures and produces normalized results."""

    def __init__(self):
        """Initialize page analyzer."""
        self.page_type_patterns = {
            "linkedin_profile": ["profile", "headline", "experience"],
            "linkedin_questions": ["question", "required", "short answer"],
            "linkedin_review": ["review", "confirmation", "submit"],
            "indeed_profile": ["profile", "resume", "skills"],
            "indeed_questions": ["question", "required"],
            "indeed_review": ["review", "confirmation"],
            "naukri_profile": ["profile", "experience", "skills"],
            "naukri_questions": ["question", "required"],
            "naukri_review": ["review", "confirmation"],
        }

    def analyze_page(self, page_data: Dict[str, Any]) -> PageAnalysisResult:
        """
        Analyze a page structure and extract information.

        Args:
            page_data: Dict with page structure (not live page)
                      Keys: url, title, forms, buttons, etc.

        Returns:
            PageAnalysisResult with normalized analysis
        """
        url = page_data.get("url", "")
        title = page_data.get("title")
        page_type = self._detect_page_type(page_data)

        log(f"[PageAnalyzer] Analyzing page: {url}")
        log(f"  - Type: {page_type}")

        # Extract forms
        forms = self._extract_forms(page_data.get("forms", []))

        # Extract fields
        visible_fields = self._extract_visible_fields(forms)
        upload_fields = self._extract_upload_fields(forms)

        # Extract buttons
        buttons = self._extract_buttons(page_data.get("buttons", []))

        # Extract navigation
        navigation_actions = self._extract_navigation(page_data)

        # Extract validation messages
        validation_messages = page_data.get("validation_messages", [])

        # Estimate completion
        completion = self._estimate_completion(page_type, len(visible_fields))

        # Determine next action hint
        next_action = self._determine_next_action(page_type, forms)

        result = PageAnalysisResult(
            page_type=page_type,
            url=url,
            title=title,
            forms=forms,
            visible_fields=visible_fields,
            upload_fields=upload_fields,
            buttons=buttons,
            navigation_actions=navigation_actions,
            validation_messages=validation_messages,
            estimated_completion=completion,
            next_action_hint=next_action,
        )

        log(f"  - Found {len(forms)} form(s)")
        log(f"  - Found {len(visible_fields)} field(s)")
        log(f"  - Estimated completion: {completion:.0%}")

        return result

    def _detect_page_type(self, page_data: Dict[str, Any]) -> str:
        """Detect page type from content using platform-aware scoring."""
        content = str(page_data).lower()
        platform = page_data.get("platform", "").lower()
        form_types = set()

        # Extract detected form types from all forms
        for form_data in page_data.get("forms", []):
            form_type = self._detect_form_type(form_data)
            if form_type != "unknown":
                form_types.add(form_type)

        # Platform-specific page type patterns
        platform_patterns = {
            "linkedin": ["linkedin_profile", "linkedin_questions", "linkedin_review"],
            "indeed": ["indeed_profile", "indeed_questions", "indeed_review"],
            "naukri": ["naukri_profile", "naukri_questions", "naukri_review"],
        }

        # Get patterns for this platform
        target_patterns = {}
        if platform in platform_patterns:
            for page_type in platform_patterns[platform]:
                if page_type in self.page_type_patterns:
                    target_patterns[page_type] = self.page_type_patterns[page_type]
        else:
            # If platform unknown, use all patterns
            target_patterns = self.page_type_patterns

        # Score only target platform page types
        scores = {}
        threshold = 0.5
        best_match = None
        best_score = 0

        for page_type, keywords in target_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in content)
            score = matches / len(keywords) if keywords else 0
            scores[page_type] = score

            if score >= threshold and score > best_score:
                best_score = score
                best_match = page_type

        # If we have a platform-specific match, use it
        if best_match:
            return best_match

        # Platform-specific fallback using form type signals
        platform_prefix = {
            "linkedin": "linkedin",
            "indeed": "indeed",
            "naukri": "naukri",
        }.get(platform, platform)

        if "upload" in form_types:
            return f"{platform_prefix}_profile"
        if "questions" in form_types:
            return f"{platform_prefix}_questions"
        if "review" in form_types:
            return f"{platform_prefix}_review"
        if "profile" in form_types:
            return f"{platform_prefix}_profile"

        # Last resort: return platform-specific application page
        if platform in ["linkedin", "indeed", "naukri"]:
            return f"{platform}_application"

        return "unknown"

    def _extract_forms(self, forms_data: List[Dict]) -> List[PageForm]:
        """Extract forms from page data."""
        forms = []

        for form_data in forms_data:
            form_id = form_data.get("id", f"form_{len(forms)}")
            form_name = form_data.get("name")
            form_type = self._detect_form_type(form_data)

            # Extract elements
            elements = []
            for elem_data in form_data.get("elements", []):
                element = PageElement(
                    element_id=elem_data.get("id", f"elem_{len(elements)}"),
                    element_type=elem_data.get("type", "unknown"),
                    label=elem_data.get("label"),
                    name=elem_data.get("name"),
                    placeholder=elem_data.get("placeholder"),
                    required=elem_data.get("required", False),
                    visible=elem_data.get("visible", True),
                    value=elem_data.get("value"),
                    options=elem_data.get("options", []),
                    validation_rules=elem_data.get("validation_rules", {}),
                )
                elements.append(element)

            # Find submit button
            submit_button = None
            for elem in elements:
                if elem.element_type == "button" and "submit" in (elem.name or "").lower():
                    submit_button = elem
                    break

            # Determine required fields
            required_fields = [
                e.element_id for e in elements if e.required and e.visible
            ]

            form = PageForm(
                form_id=form_id,
                form_name=form_name,
                form_type=form_type,
                elements=elements,
                submit_button=submit_button,
                required_fields=required_fields,
            )
            forms.append(form)

        return forms

    def _detect_form_type(self, form_data: Dict) -> str:
        """Detect form type from form data."""
        content = str(form_data).lower()

        if "upload" in content or "resume" in content:
            return "upload"
        elif "question" in content:
            return "questions"
        elif "profile" in content or "name" in content:
            return "profile"
        elif "review" in content or "confirm" in content:
            return "review"
        else:
            return "unknown"

    def _extract_visible_fields(self, forms: List[PageForm]) -> List[str]:
        """Extract all visible field IDs."""
        fields = []
        for form in forms:
            for element in form.elements:
                if element.visible and element.element_type in ["input", "textarea", "select"]:
                    fields.append(element.element_id)
        return fields

    def _extract_upload_fields(self, forms: List[PageForm]) -> List[str]:
        """Extract upload field IDs."""
        fields = []
        for form in forms:
            for element in form.elements:
                if element.element_type == "file":
                    fields.append(element.element_id)
        return fields

    def _extract_buttons(self, buttons_data: List[Dict]) -> List[PageElement]:
        """Extract buttons from page data."""
        buttons = []
        for btn_data in buttons_data:
            button = PageElement(
                element_id=btn_data.get("id", f"btn_{len(buttons)}"),
                element_type="button",
                label=btn_data.get("label") or btn_data.get("text"),
                name=btn_data.get("name"),
                visible=btn_data.get("visible", True),
            )
            buttons.append(button)
        return buttons

    def _extract_navigation(self, page_data: Dict) -> List[str]:
        """Extract navigation actions from page data."""
        actions = []

        # Check for navigation elements
        if page_data.get("has_next_button"):
            actions.append("continue")
        if page_data.get("has_back_button"):
            actions.append("back")
        if page_data.get("has_save_button"):
            actions.append("save_and_continue")
        if page_data.get("has_submit_button"):
            actions.append("submit")

        return actions

    def _estimate_completion(self, page_type: str, field_count: int) -> float:
        """Estimate application completion percentage."""
        if page_type == "unknown":
            return 0.0
        elif page_type.endswith("_review"):
            return 0.8
        elif page_type.endswith("_questions"):
            return 0.6
        elif page_type.endswith("_profile"):
            return 0.3
        else:
            return 0.5

    def _determine_next_action(self, page_type: str, forms: List[PageForm]) -> Optional[str]:
        """Determine hint about next required action."""
        if not forms:
            return None

        for form in forms:
            if form.form_type == "upload":
                return "upload_document"
            elif form.form_type == "questions":
                return "answer_questions"
            elif form.form_type == "profile":
                return "fill_profile"
            elif form.form_type == "review":
                return "review_and_submit"

        return None


class PageAnalysisCache:
    """Caches page analysis results."""

    def __init__(self):
        """Initialize cache."""
        self.cache: Dict[str, PageAnalysisResult] = {}

    def get(self, page_url: str) -> Optional[PageAnalysisResult]:
        """Get cached analysis for URL."""
        return self.cache.get(page_url)

    def cache_analysis(self, url: str, analysis: PageAnalysisResult) -> None:
        """Cache analysis result."""
        self.cache[url] = analysis

    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()


def create_page_analyzer() -> PageAnalyzer:
    """Factory function to create page analyzer."""
    return PageAnalyzer()

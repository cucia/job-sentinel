"""
Page Data Producer

Transforms raw page source into normalized page_data contract.

Browser-independent extraction layer for:
- Forms and fields
- Buttons and navigation
- Page type detection
- Platform-specific rules

Input: raw_page dict with url, title, html, platform
Output: page_data dict with strict contract
"""

from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
import re


class PageDataContract:
    """Strict page_data contract definition."""

    @staticmethod
    def create(
        url: str,
        title: str,
        platform: str,
        forms: List[Dict] = None,
        fields: List[Dict] = None,
        buttons: List[Dict] = None,
        links: List[Dict] = None,
        page_type: str = "unknown",
        metadata: Dict = None,
    ) -> dict:
        """
        Create page_data following strict contract.

        All outputs must follow this exact structure.
        No additional top-level fields permitted.
        """
        return {
            "url": url,
            "title": title,
            "platform": platform,
            "forms": forms or [],
            "fields": fields or [],
            "buttons": buttons or [],
            "links": links or [],
            "page_type": page_type,
            "metadata": metadata or {},
        }


class PageDataProducer:
    """Transform raw page source into normalized page_data."""

    PLATFORM_EXTRACTORS = {
        "linkedin": "extract_linkedin",
        "indeed": "extract_indeed",
        "naukri": "extract_naukri",
    }

    def __init__(self):
        """Initialize producer."""
        pass

    def produce(self, raw_page: dict) -> dict:
        """
        Transform raw page into page_data.

        Args:
            raw_page: {
                "url": str,
                "title": str,
                "html": str,
                "platform": str
            }

        Returns:
            page_data: Normalized contract
        """
        url = raw_page.get("url", "")
        title = raw_page.get("title", "")
        html = raw_page.get("html", "")
        platform = raw_page.get("platform", "").lower()

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Platform-specific extraction
        extractor_name = self.PLATFORM_EXTRACTORS.get(platform)
        if extractor_name and hasattr(self, extractor_name):
            extractor = getattr(self, extractor_name)
            forms, fields, buttons, links, page_type = extractor(soup, url, title)
        else:
            # Generic extraction
            forms, fields, buttons, links, page_type = self._extract_generic(soup, url, title)

        # Build page_data following strict contract
        page_data = PageDataContract.create(
            url=url,
            title=title,
            platform=platform,
            forms=forms,
            fields=fields,
            buttons=buttons,
            links=links,
            page_type=page_type,
            metadata={"extraction_platform": platform},
        )

        return page_data

    def extract_linkedin(self, soup, url: str, title: str):
        """LinkedIn-specific extraction."""
        forms = self._extract_forms(soup)
        fields = self._extract_fields(soup)
        buttons = self._extract_buttons(soup)
        links = self._extract_links(soup)

        # Detect LinkedIn page type
        page_type = self._detect_linkedin_page_type(url, title, soup)

        return forms, fields, buttons, links, page_type

    def extract_indeed(self, soup, url: str, title: str):
        """Indeed-specific extraction."""
        forms = self._extract_forms(soup)
        fields = self._extract_fields(soup)
        buttons = self._extract_buttons(soup)
        links = self._extract_links(soup)

        # Detect Indeed page type
        page_type = self._detect_indeed_page_type(url, title, soup)

        return forms, fields, buttons, links, page_type

    def extract_naukri(self, soup, url: str, title: str):
        """Naukri-specific extraction."""
        forms = self._extract_forms(soup)
        fields = self._extract_fields(soup)
        buttons = self._extract_buttons(soup)
        links = self._extract_links(soup)

        # Detect Naukri page type
        page_type = self._detect_naukri_page_type(url, title, soup)

        return forms, fields, buttons, links, page_type

    def _extract_generic(self, soup, url: str, title: str):
        """Generic extraction for unknown platforms."""
        forms = self._extract_forms(soup)
        fields = self._extract_fields(soup)
        buttons = self._extract_buttons(soup)
        links = self._extract_links(soup)
        page_type = "generic_form"

        return forms, fields, buttons, links, page_type

    def _extract_forms(self, soup) -> List[Dict]:
        """Extract all forms from page."""
        forms = []

        for form in soup.find_all("form"):
            form_dict = {
                "id": form.get("id", f"form_{len(forms)}"),
                "name": form.get("name", ""),
                "action": form.get("action", ""),
                "method": form.get("method", "post").lower(),
                "elements": [],
            }

            # Extract form elements
            for elem in form.find_all(["input", "select", "textarea"]):
                form_dict["elements"].append(self._extract_element(elem))

            forms.append(form_dict)

        return forms

    def _extract_fields(self, soup) -> List[Dict]:
        """Extract all input fields from page."""
        fields = []
        seen_ids = set()

        for elem in soup.find_all(["input", "select", "textarea"]):
            field = self._extract_element(elem)

            # Avoid duplicates
            field_id = field.get("id", field.get("name", ""))
            if field_id and field_id in seen_ids:
                continue
            seen_ids.add(field_id)

            fields.append(field)

        return fields

    def _extract_element(self, elem) -> Dict:
        """Extract field element properties."""
        elem_type = elem.name.lower()

        # Map HTML element types to page_data types
        type_map = {
            "input": elem.get("type", "text").lower(),
            "select": "select",
            "textarea": "textarea",
        }
        field_type = type_map.get(elem_type, elem_type)

        element = {
            "id": elem.get("id", ""),
            "type": field_type,
            "name": elem.get("name", ""),
            "label": self._extract_label(elem),
            "required": elem.has_attr("required"),
            "visible": self._is_visible(elem),
            "placeholder": elem.get("placeholder", ""),
            "value": elem.get("value", ""),
        }

        # Extract options for select/radio/checkbox
        if field_type == "select":
            options = []
            for option in elem.find_all("option"):
                options.append({
                    "value": option.get("value", ""),
                    "text": option.get_text(strip=True),
                    "selected": option.has_attr("selected"),
                })
            element["options"] = options
        elif field_type in ("radio", "checkbox"):
            element["options"] = [
                {"value": elem.get("value", ""), "text": self._extract_label(elem)}
            ]

        return element

    def _extract_label(self, elem) -> str:
        """Extract label for form element."""
        # Check for associated label element
        elem_id = elem.get("id")
        if elem_id:
            label = elem.find_parent("form")
            if label:
                label = label.find("label", {"for": elem_id})
                if label:
                    return label.get_text(strip=True)

        # Check for label wrapping the element
        parent = elem.find_parent("label")
        if parent:
            return parent.get_text(strip=True)

        # Check for aria-label
        if elem.has_attr("aria-label"):
            return elem.get("aria-label", "")

        # Check for title
        if elem.has_attr("title"):
            return elem.get("title", "")

        return ""

    def _extract_buttons(self, soup) -> List[Dict]:
        """Extract all buttons from page."""
        buttons = []

        for button in soup.find_all(["button", "input"]):
            # Skip input buttons that aren't button/submit/reset
            if button.name == "input":
                input_type = button.get("type", "").lower()
                if input_type not in ("button", "submit", "reset"):
                    continue

            button_dict = {
                "id": button.get("id", f"button_{len(buttons)}"),
                "type": button.get("type", "button").lower(),
                "text": button.get_text(strip=True) or button.get("value", ""),
                "name": button.get("name", ""),
            }

            buttons.append(button_dict)

        return buttons

    def _extract_links(self, soup) -> List[Dict]:
        """Extract navigation links from page."""
        links = []

        for link in soup.find_all("a", href=True):
            link_dict = {
                "href": link.get("href", ""),
                "text": link.get_text(strip=True),
                "title": link.get("title", ""),
            }

            links.append(link_dict)

        return links

    def _is_visible(self, elem) -> bool:
        """Check if element is visible (not hidden)."""
        # Check for display:none
        style = elem.get("style", "").lower()
        if "display:none" in style or "display: none" in style:
            return False

        # Check for hidden attribute
        if elem.has_attr("hidden"):
            return False

        # Check parent visibility
        parent = elem.find_parent()
        if parent and parent.has_attr("hidden"):
            return False

        return True

    def _detect_linkedin_page_type(self, url: str, title: str, soup) -> str:
        """Detect LinkedIn page type."""
        url_lower = url.lower()
        title_lower = title.lower()

        # Profile page
        if "/myprofile/" in url_lower or "profile" in title_lower:
            return "linkedin_profile"

        # Questions/questionnaire
        if "/questionnaire" in url_lower or "question" in title_lower:
            return "linkedin_questions"

        # Review page
        if "/review" in url_lower or "review" in title_lower:
            return "linkedin_review"

        # Application page (default for LinkedIn)
        if "/apply" in url_lower or "/jobs/" in url_lower:
            return "linkedin_application"

        return "linkedin_application"

    def _detect_indeed_page_type(self, url: str, title: str, soup) -> str:
        """Detect Indeed page type."""
        url_lower = url.lower()
        title_lower = title.lower()

        # Resume/profile
        if "resume" in title_lower or "profile" in title_lower:
            return "indeed_profile"

        # Questions
        if "question" in title_lower:
            return "indeed_questions"

        # Application
        if "/apply" in url_lower or "apply" in title_lower:
            return "indeed_application"

        return "indeed_application"

    def _detect_naukri_page_type(self, url: str, title: str, soup) -> str:
        """Detect Naukri page type."""
        url_lower = url.lower()
        title_lower = title.lower()

        # Profile
        if "/profile" in url_lower or "profile" in title_lower:
            return "naukri_profile"

        # Application
        if "/apply" in url_lower or "apply" in title_lower:
            return "naukri_application"

        return "naukri_application"


def create_page_data_producer() -> PageDataProducer:
    """Factory function to create producer."""
    return PageDataProducer()

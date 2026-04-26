"""
ATS Field Mapping System

Predefined field selectors and mappings for popular Applicant Tracking Systems.
These mappings are used before generic form detection to improve accuracy.
"""

from typing import Dict, List, Optional


class ATSFieldMap:
    """Field mapping for a specific ATS platform."""

    def __init__(self, name: str, selectors: Dict[str, str], patterns: Dict[str, List[str]]):
        self.name = name
        self.selectors = selectors  # Direct CSS selectors
        self.patterns = patterns    # Field name patterns for fallback


# Greenhouse ATS
GREENHOUSE_MAP = ATSFieldMap(
    name="greenhouse",
    selectors={
        "first_name": "input#first_name",
        "last_name": "input#last_name",
        "email": "input#email",
        "phone": "input#phone",
        "resume": "input[type='file'][name='resume']",
        "cover_letter": "textarea#cover_letter",
        "linkedin": "input#question_",  # Varies, use pattern
        "website": "input[name*='website']",
        "location": "input#location",
    },
    patterns={
        "first_name": ["first name", "firstname", "given name"],
        "last_name": ["last name", "lastname", "surname", "family name"],
        "email": ["email", "e-mail"],
        "phone": ["phone", "mobile", "telephone", "contact number"],
        "resume": ["resume", "cv", "curriculum vitae"],
        "cover_letter": ["cover letter", "covering letter", "motivation"],
        "linkedin": ["linkedin", "linkedin profile", "linkedin url"],
        "website": ["website", "portfolio", "personal site"],
    }
)


# Lever ATS
LEVER_MAP = ATSFieldMap(
    name="lever",
    selectors={
        "name": "input[name='name']",
        "email": "input[name='email']",
        "phone": "input[name='phone']",
        "resume": "input[type='file'][name='resume']",
        "cover_letter": "textarea[name='comments']",
        "linkedin": "input[name='urls[LinkedIn]']",
        "github": "input[name='urls[GitHub]']",
        "website": "input[name='urls[Portfolio]']",
    },
    patterns={
        "name": ["full name", "name"],
        "email": ["email"],
        "phone": ["phone", "mobile"],
        "resume": ["resume", "cv"],
        "cover_letter": ["additional information", "comments", "cover letter"],
        "linkedin": ["linkedin"],
        "github": ["github"],
        "website": ["portfolio", "website"],
    }
)


# Workday ATS
WORKDAY_MAP = ATSFieldMap(
    name="workday",
    selectors={
        "first_name": "input[data-automation-id*='firstName']",
        "last_name": "input[data-automation-id*='lastName']",
        "email": "input[data-automation-id*='email']",
        "phone": "input[data-automation-id*='phone']",
        "resume": "input[type='file'][data-automation-id*='resume']",
        "cover_letter": "textarea[data-automation-id*='coverLetter']",
        "address": "input[data-automation-id*='address']",
        "city": "input[data-automation-id*='city']",
        "country": "select[data-automation-id*='country']",
    },
    patterns={
        "first_name": ["first name", "given name"],
        "last_name": ["last name", "surname"],
        "email": ["email"],
        "phone": ["phone", "mobile"],
        "resume": ["resume", "cv"],
        "cover_letter": ["cover letter"],
        "address": ["address", "street"],
        "city": ["city"],
        "country": ["country"],
    }
)


# Generic/Unknown ATS
GENERIC_MAP = ATSFieldMap(
    name="generic",
    selectors={},
    patterns={
        "first_name": ["first name", "firstname", "given name", "fname"],
        "last_name": ["last name", "lastname", "surname", "family name", "lname"],
        "email": ["email", "e-mail", "email address"],
        "phone": ["phone", "mobile", "telephone", "contact number", "phone number"],
        "resume": ["resume", "cv", "curriculum vitae", "upload resume"],
        "cover_letter": ["cover letter", "covering letter", "motivation letter", "message"],
        "linkedin": ["linkedin", "linkedin profile", "linkedin url"],
        "github": ["github", "github profile", "github url"],
        "website": ["website", "portfolio", "personal site", "personal website"],
        "location": ["location", "city", "current location"],
        "experience": ["years of experience", "experience", "work experience"],
        "education": ["education", "degree", "qualification"],
    }
)


# ATS Registry
ATS_MAPS = {
    "greenhouse": GREENHOUSE_MAP,
    "lever": LEVER_MAP,
    "workday": WORKDAY_MAP,
    "generic": GENERIC_MAP,
}


def get_field_map(ats_type: str) -> ATSFieldMap:
    """
    Get field map for specific ATS type.

    Args:
        ats_type: ATS platform name (greenhouse, lever, workday, generic)

    Returns:
        ATSFieldMap object
    """
    return ATS_MAPS.get(ats_type.lower(), GENERIC_MAP)


def detect_ats_from_url(url: str) -> Optional[str]:
    """
    Detect ATS type from URL.

    Args:
        url: Page URL

    Returns:
        ATS type name or None
    """
    url_lower = url.lower()

    if "greenhouse.io" in url_lower or "boards.greenhouse.io" in url_lower:
        return "greenhouse"
    elif "lever.co" in url_lower or "jobs.lever.co" in url_lower:
        return "lever"
    elif "myworkdayjobs.com" in url_lower or "workday.com" in url_lower:
        return "workday"
    else:
        return None


def detect_ats_from_page(page_content: str) -> Optional[str]:
    """
    Detect ATS type from page content.

    Args:
        page_content: HTML content or page text

    Returns:
        ATS type name or None
    """
    content_lower = page_content.lower()

    # Check for ATS-specific markers
    if "greenhouse" in content_lower and ("grnhse" in content_lower or "greenhouse.io" in content_lower):
        return "greenhouse"
    elif "lever" in content_lower and ("lever.co" in content_lower or "lever-application" in content_lower):
        return "lever"
    elif "workday" in content_lower and ("myworkdayjobs" in content_lower or "workday application" in content_lower):
        return "workday"
    else:
        return None


async def find_field_by_map(page, field_name: str, ats_map: ATSFieldMap):
    """
    Find form field using ATS-specific mapping.

    Args:
        page: Playwright page object
        field_name: Field name (e.g., "email", "resume")
        ats_map: ATSFieldMap object

    Returns:
        Playwright element or None
    """
    # Try direct selector first
    if field_name in ats_map.selectors:
        selector = ats_map.selectors[field_name]
        try:
            element = await page.query_selector(selector)
            if element:
                return element
        except Exception:
            pass

    # Try pattern matching
    if field_name in ats_map.patterns:
        patterns = ats_map.patterns[field_name]
        all_inputs = await page.query_selector_all("input, textarea, select")

        for input_el in all_inputs:
            try:
                # Check name attribute
                name_attr = await input_el.get_attribute("name")
                if name_attr:
                    name_lower = name_attr.lower()
                    if any(pattern in name_lower for pattern in patterns):
                        return input_el

                # Check id attribute
                id_attr = await input_el.get_attribute("id")
                if id_attr:
                    id_lower = id_attr.lower()
                    if any(pattern in id_lower for pattern in patterns):
                        return input_el

                # Check placeholder
                placeholder = await input_el.get_attribute("placeholder")
                if placeholder:
                    placeholder_lower = placeholder.lower()
                    if any(pattern in placeholder_lower for pattern in patterns):
                        return input_el

                # Check label
                field_id = await input_el.get_attribute("id")
                if field_id:
                    label = await page.query_selector(f"label[for='{field_id}']")
                    if label:
                        label_text = await label.text_content()
                        if label_text:
                            label_lower = label_text.lower()
                            if any(pattern in label_lower for pattern in patterns):
                                return input_el

            except Exception:
                continue

    return None


def get_common_field_names() -> List[str]:
    """Get list of common field names across all ATS platforms."""
    return [
        "first_name",
        "last_name",
        "email",
        "phone",
        "resume",
        "cover_letter",
        "linkedin",
        "github",
        "website",
        "location",
        "experience",
        "education",
    ]

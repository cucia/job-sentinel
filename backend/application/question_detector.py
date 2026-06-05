"""
Question Detector

Scans page DOM to detect and extract questions.
Associates question text with form fields.
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Question:
    """Represents a detected question."""
    text: str
    field_type: str  # text, textarea, select, radio, checkbox
    selector: str
    options: Optional[List[str]] = None
    label: Optional[str] = None


class QuestionDetector:
    """Detects questions on a page."""

    async def detect_questions(self, adapter) -> List[Question]:
        """
        Detect questions on current page.

        Args:
            adapter: PlaywrightAdapter instance

        Returns:
            List of detected Question objects
        """
        questions = []
        page = await adapter.get_page()
        html = page.html

        # Detect text inputs with labels
        text_inputs = await self._find_elements_with_labels(adapter, 'input[type="text"]')
        for selector, label in text_inputs:
            questions.append(Question(
                text=label,
                field_type="text",
                selector=selector,
                label=label
            ))

        # Detect textareas with labels
        textareas = await self._find_elements_with_labels(adapter, 'textarea')
        for selector, label in textareas:
            questions.append(Question(
                text=label,
                field_type="textarea",
                selector=selector,
                label=label
            ))

        # Detect select dropdowns with labels and options
        selects = await self._find_elements_with_labels(adapter, 'select')
        for selector, label in selects:
            options = await self._get_select_options(adapter, selector)
            questions.append(Question(
                text=label,
                field_type="select",
                selector=selector,
                options=options,
                label=label
            ))

        # Detect radio groups
        radio_groups = await self._detect_radio_groups(adapter)
        for group_name, selector, label, options in radio_groups:
            questions.append(Question(
                text=label,
                field_type="radio",
                selector=selector,
                options=options,
                label=label
            ))

        # Detect checkboxes with labels
        checkboxes = await self._find_elements_with_labels(adapter, 'input[type="checkbox"]')
        for selector, label in checkboxes:
            questions.append(Question(
                text=label,
                field_type="checkbox",
                selector=selector,
                label=label
            ))

        return questions

    async def _find_elements_with_labels(self, adapter, selector: str) -> List[tuple]:
        """Find elements and their associated labels."""
        results = []
        elements = await adapter.find_elements(selector)

        for element in elements:
            element_id = await element.get_attribute("id")
            if not element_id:
                continue

            # Find associated label
            label_selector = f'label[for="{element_id}"]'
            label_element = await adapter.find_element(label_selector)

            if label_element:
                label_text = await label_element.get_text()
                # Fix: Generate clean selector from element ID
                clean_selector = f'#{element_id}'
                results.append((clean_selector, label_text))

        return results

    async def _get_select_options(self, adapter, select_selector: str) -> List[str]:
        """Get options from a select element."""
        options = []
        option_elements = await adapter.find_elements(f'{select_selector} option')

        for opt in option_elements:
            value = await opt.get_attribute("value")
            if value:
                options.append(value)

        return options

    async def _detect_radio_groups(self, adapter) -> List[tuple]:
        """Detect radio button groups."""
        radio_groups = []
        radios = await adapter.find_elements('input[type="radio"]')

        processed_groups = set()

        for radio in radios:
            name = await radio.get_attribute("name")
            if not name or name in processed_groups:
                continue

            processed_groups.add(name)

            # Find all radios in this group
            group_radios = await adapter.find_elements(f'input[type="radio"][name="{name}"]')
            options = []

            for group_radio in group_radios:
                value = await group_radio.get_attribute("value")
                if value:
                    options.append(value)

            # Find label for group (use fieldset or first radio's parent)
            first_radio_id = await group_radios[0].get_attribute("id")
            label_text = name

            if first_radio_id:
                label_element = await adapter.find_element(f'label[for="{first_radio_id}"]')
                if label_element:
                    label_text = await label_element.get_text()

            # Fix: Use selector that targets group by name, not individual radio
            # When executing, ActionExecutor will select specific value
            group_selector = f'input[type="radio"][name="{name}"]'

            radio_groups.append((
                name,
                group_selector,
                label_text,
                options
            ))

        return radio_groups

"""
LinkedIn Question Integrator

Integrates LinkedIn application forms with the Dynamic Question Engine.
Converts detected LinkedIn questions into ExecutionPlanSteps.

Reuses:
- QuestionDetector
- QuestionClassifier
- AnswerMapper
- ExecutionPlanStep
"""

import logging
import re
from typing import Optional, List, Dict, Any
from html.parser import HTMLParser

from backend.application.question_detector import Question
from backend.application.question_classifier import QuestionClassifier, QuestionCategory
from backend.application.answer_mapper import AnswerMapper
from backend.application.session import ExecutionPlanStep, ExecutionAction, ExecutionPlan
from backend.platforms.linkedin.linkedin_page_data import LinkedInPageData

logger = logging.getLogger(__name__)


class HTMLQuestionParser:
    """Parses HTML to extract form questions without requiring browser adapter."""

    def __init__(self):
        """Initialize parser."""
        pass

    def extract_questions(self, html: str) -> List[Question]:
        """
        Extract questions from HTML.

        Args:
            html: HTML content

        Returns:
            List of Question objects
        """
        questions = []

        logger.info(f"[HTMLQuestionParser] Starting extraction from {len(html)} bytes of HTML")

        # Parse labels and associate with form elements
        label_pattern = r'<label[^>]*(?:for="([^"]*)")?[^>]*>([^<]+)</label>'
        label_matches = list(re.finditer(label_pattern, html, re.IGNORECASE))
        logger.info(f"[HTMLQuestionParser] Found {len(label_matches)} labels")

        label_map = {}
        for match in label_matches:
            for_id = match.group(1)
            label_text = match.group(2).strip()
            if for_id:
                label_map[for_id] = label_text
                logger.info(f"[HTMLQuestionParser] Label for '{for_id}': '{label_text}'")

        # Extract input fields (order-independent regex)
        input_pattern = r'<input\s+([^>]*?)(?:type="([^"]*)"[^>]*|[^>]*type="([^"]*)"[^>]*)\s*>'
        # Better approach: match input and extract attributes separately
        input_pattern = r'<input[^>]*>'
        input_matches = list(re.finditer(input_pattern, html, re.IGNORECASE))
        logger.info(f"[HTMLQuestionParser] Found {len(input_matches)} input elements")

        for match in input_matches:
            input_tag = match.group(0)

            # Extract attributes
            type_match = re.search(r'type="([^"]*)"', input_tag, re.IGNORECASE)
            id_match = re.search(r'id="([^"]*)"', input_tag, re.IGNORECASE)
            name_match = re.search(r'name="([^"]*)"', input_tag, re.IGNORECASE)

            field_type = type_match.group(1) if type_match else "text"
            input_id = id_match.group(1) if id_match else ""
            input_name = name_match.group(1) if name_match else ""

            # Skip submit buttons and hidden fields
            if field_type in ("submit", "button", "hidden"):
                logger.info(f"[HTMLQuestionParser] Skipping {field_type} input")
                continue

            selector = f"#{input_id}" if input_id else f'input[name="{input_name}"]' if input_name else ""
            if not selector:
                logger.info(f"[HTMLQuestionParser] No selector for input")
                continue

            # Get label text
            label_text = label_map.get(input_id, input_name or "")
            if not label_text:
                label_text = input_name.replace("_", " ").title() if input_name else ""

            if label_text:
                q = Question(
                    text=label_text,
                    field_type=field_type,
                    selector=selector,
                    label=label_text,
                )
                questions.append(q)
                logger.info(f"[HTMLQuestionParser] Input: {label_text} ({field_type}) @ {selector}")

        # Extract textarea fields
        textarea_pattern = r'<textarea[^>]*>'
        textarea_matches = list(re.finditer(textarea_pattern, html, re.IGNORECASE))
        logger.info(f"[HTMLQuestionParser] Found {len(textarea_matches)} textarea elements")

        for match in textarea_matches:
            textarea_tag = match.group(0)

            # Extract attributes
            id_match = re.search(r'id="([^"]*)"', textarea_tag, re.IGNORECASE)
            name_match = re.search(r'name="([^"]*)"', textarea_tag, re.IGNORECASE)

            textarea_id = id_match.group(1) if id_match else ""
            textarea_name = name_match.group(1) if name_match else ""

            selector = f"#{textarea_id}" if textarea_id else f'textarea[name="{textarea_name}"]' if textarea_name else ""
            if not selector:
                continue

            label_text = label_map.get(textarea_id, textarea_name or "")
            if not label_text:
                label_text = textarea_name.replace("_", " ").title() if textarea_name else ""

            if label_text:
                q = Question(
                    text=label_text,
                    field_type="textarea",
                    selector=selector,
                    label=label_text,
                )
                questions.append(q)
                logger.info(f"[HTMLQuestionParser] Textarea: {label_text} @ {selector}")

        # Extract select fields
        select_pattern = r'<select[^>]*>(.*?)</select>'
        select_matches = list(re.finditer(select_pattern, html, re.IGNORECASE | re.DOTALL))
        logger.info(f"[HTMLQuestionParser] Found {len(select_matches)} select elements")

        for match in select_matches:
            select_tag_start = html.rfind('<select', 0, match.start())
            select_tag_end = html.find('>', select_tag_start)
            select_tag = html[select_tag_start:select_tag_end+1]

            # Extract attributes
            id_match = re.search(r'id="([^"]*)"', select_tag, re.IGNORECASE)
            name_match = re.search(r'name="([^"]*)"', select_tag, re.IGNORECASE)

            select_id = id_match.group(1) if id_match else ""
            select_name = name_match.group(1) if name_match else ""

            selector = f"#{select_id}" if select_id else f'select[name="{select_name}"]' if select_name else ""
            if not selector:
                continue

            # Extract options
            options_html = match.group(1)
            option_pattern = r'<option[^>]*value="([^"]*)"[^>]*>([^<]+)</option>'
            options = []
            for opt_match in re.finditer(option_pattern, options_html, re.IGNORECASE):
                options.append(opt_match.group(2).strip())

            label_text = label_map.get(select_id, select_name or "")
            if not label_text:
                label_text = select_name.replace("_", " ").title() if select_name else ""

            if label_text:
                q = Question(
                    text=label_text,
                    field_type="select",
                    selector=selector,
                    options=options if options else None,
                    label=label_text,
                )
                questions.append(q)
                logger.info(f"[HTMLQuestionParser] Select: {label_text} ({len(options)} options) @ {selector}")

        # Extract radio buttons
        radio_pattern = r'<input[^>]*type="radio"[^>]*>'
        radio_matches = list(re.finditer(radio_pattern, html, re.IGNORECASE))
        logger.info(f"[HTMLQuestionParser] Found {len(radio_matches)} radio elements")

        radio_names_seen = set()
        for match in radio_matches:
            radio_tag = match.group(0)

            # Extract attributes
            id_match = re.search(r'id="([^"]*)"', radio_tag, re.IGNORECASE)
            name_match = re.search(r'name="([^"]*)"', radio_tag, re.IGNORECASE)

            radio_id = id_match.group(1) if id_match else ""
            radio_name = name_match.group(1) if name_match else ""

            if radio_name in radio_names_seen:
                continue
            radio_names_seen.add(radio_name)

            selector = f'input[name="{radio_name}"]' if radio_name else f"#{radio_id}" if radio_id else ""
            if not selector:
                continue

            label_text = label_map.get(radio_id, radio_name or "")
            if not label_text:
                label_text = radio_name.replace("_", " ").title() if radio_name else ""

            if label_text:
                q = Question(
                    text=label_text,
                    field_type="radio",
                    selector=selector,
                    label=label_text,
                )
                questions.append(q)
                logger.info(f"[HTMLQuestionParser] Radio: {label_text} @ {selector}")

        # Extract checkboxes
        checkbox_pattern = r'<input[^>]*type="checkbox"[^>]*>'
        checkbox_matches = list(re.finditer(checkbox_pattern, html, re.IGNORECASE))
        logger.info(f"[HTMLQuestionParser] Found {len(checkbox_matches)} checkbox elements")

        checkbox_names_seen = set()
        for match in checkbox_matches:
            checkbox_tag = match.group(0)

            # Extract attributes
            id_match = re.search(r'id="([^"]*)"', checkbox_tag, re.IGNORECASE)
            name_match = re.search(r'name="([^"]*)"', checkbox_tag, re.IGNORECASE)

            checkbox_id = id_match.group(1) if id_match else ""
            checkbox_name = name_match.group(1) if name_match else ""

            if checkbox_name in checkbox_names_seen:
                continue
            checkbox_names_seen.add(checkbox_name)

            selector = f'input[name="{checkbox_name}"]' if checkbox_name else f"#{checkbox_id}" if checkbox_id else ""
            if not selector:
                continue

            label_text = label_map.get(checkbox_id, checkbox_name or "")
            if not label_text:
                label_text = checkbox_name.replace("_", " ").title() if checkbox_name else ""

            if label_text:
                q = Question(
                    text=label_text,
                    field_type="checkbox",
                    selector=selector,
                    label=label_text,
                )
                questions.append(q)
                logger.info(f"[HTMLQuestionParser] Checkbox: {label_text} @ {selector}")

        logger.info(f"[HTMLQuestionParser] Total questions extracted: {len(questions)}")
        return questions


class LinkedInQuestionIntegrator:
    """Integrates LinkedIn questions with Dynamic Question Engine."""

    def __init__(self):
        """Initialize integrator with existing components."""
        self.classifier = QuestionClassifier()
        self.answer_mapper = AnswerMapper()
        self.html_parser = HTMLQuestionParser()

    async def detect_linkedin_questions(self, html: str) -> List[Question]:
        """
        Detect questions in LinkedIn application form.

        Uses HTML parsing bridge to extract questions without requiring browser adapter.

        Args:
            html: Page HTML content

        Returns:
            List of detected Question objects
        """
        logger.info("[LinkedInQuestionIntegrator] Detecting LinkedIn questions from HTML")

        questions = self.html_parser.extract_questions(html)
        logger.info(f"[LinkedInQuestionIntegrator] Detected {len(questions)} questions")

        for q in questions:
            logger.info(f"[LinkedInQuestionIntegrator] Q: {q.text} ({q.field_type})")

        return questions

    def classify_linkedin_questions(
        self, questions: List[Question]
    ) -> List[tuple]:
        """
        Classify detected LinkedIn questions.

        Args:
            questions: List of detected Question objects

        Returns:
            List of (question, category) tuples
        """
        logger.info(f"[LinkedInQuestionIntegrator] Classifying {len(questions)} questions")

        classified = []
        for question in questions:
            # QuestionClassifier.classify() expects question text (string), not Question object
            category = self.classifier.classify(question.text)
            classified.append((question, category))
            logger.info(
                f"[LinkedInQuestionIntegrator] {question.text[:40]} → {category}"
            )

        return classified

    def map_linkedin_answers(
        self, classified_questions: List[tuple]
    ) -> Dict[str, str]:
        """
        Map answers for classified LinkedIn questions.

        Args:
            classified_questions: List of (question, category) tuples

        Returns:
            Dictionary mapping selectors to answers
        """
        logger.info(
            f"[LinkedInQuestionIntegrator] Mapping answers for {len(classified_questions)} questions"
        )

        answers = {}
        for question, category in classified_questions:
            # Get answer for category
            answer = self.answer_mapper.get_answer(category)

            # Handle field-specific formatting
            if question.field_type in ("select", "radio", "checkbox", "number"):
                if question.field_type == "number":
                    # Format for numeric input fields
                    answer = self.answer_mapper.get_answer_for_field_type(
                        category, question.field_type, None
                    )
                elif question.options:
                    # Format for select/radio/checkbox with options
                    answer = self.answer_mapper.get_answer_for_field_type(
                        category, question.field_type, question.options
                    )

            answers[question.selector] = answer
            logger.info(
                f"[LinkedInQuestionIntegrator] {question.text[:40]} → {answer}"
            )

        return answers

    async def generate_question_steps(
        self,
        questions: List[Question],
        start_step_number: int = 1,
    ) -> List[ExecutionPlanStep]:
        """
        Generate ExecutionPlanSteps for detected questions.

        Detects multi-step wizard forms and inserts CONTINUE_TO_NEXT_STEP actions
        between wizard sections to make hidden fields visible before filling.

        Args:
            questions: List of detected Question objects
            start_step_number: Starting step number

        Returns:
            List of ExecutionPlanSteps with CONTINUE actions inserted
        """
        logger.info(
            f"[LinkedInQuestionIntegrator] Generating {len(questions)} execution steps"
        )

        # Classify questions
        classified = self.classify_linkedin_questions(questions)

        # Map answers
        answers = self.map_linkedin_answers(classified)

        # Detect wizard steps by grouping fields by their parent step div
        fields_by_step = self._group_fields_by_wizard_step(questions)

        # Generate steps with CONTINUE actions between wizard steps
        steps = []
        step_num = start_step_number

        if fields_by_step:
            # Multi-step wizard detected - insert CONTINUE actions
            logger.info(
                f"[LinkedInQuestionIntegrator] Multi-step wizard detected: {len(fields_by_step)} steps"
            )

            for wizard_step_num, step_fields in sorted(fields_by_step.items()):
                # Add fields for this wizard step
                for question in step_fields:
                    # Find category for this question
                    category = None
                    for q, cat in classified:
                        if q.selector == question.selector:
                            category = cat
                            break

                    if question.field_type == "file":
                        continue

                    answer = answers.get(question.selector, "")

                    # Determine action based on field type
                    if question.field_type == "textarea":
                        action = ExecutionAction.FILL_PROFILE
                    elif question.field_type in ("select", "radio", "checkbox"):
                        action = ExecutionAction.SELECT_OPTIONS
                    else:
                        action = ExecutionAction.FILL_PROFILE

                    step = ExecutionPlanStep(
                        step_number=step_num,
                        action=action,
                        description=f"Answer: {question.text}",
                        selector=question.selector,
                        field_name=question.label or question.text,
                        expected_value=answer,
                        value_source="mapped",
                        required=False,
                        metadata={
                            "platform": "linkedin",
                            "question_type": question.field_type,
                            "question_category": str(category) if category else "unknown",
                            "original_text": question.text,
                            "wizard_step": wizard_step_num,
                        },
                    )
                    steps.append(step)
                    step_num += 1

                # Add CONTINUE action after each wizard step (except the last one)
                # Special case: Add extra CONTINUE after last field step to reach review page
                if wizard_step_num < max(fields_by_step.keys()):
                    continue_step = ExecutionPlanStep(
                        step_number=step_num,
                        action=ExecutionAction.CONTINUE_TO_NEXT_STEP,
                        description=f"Continue to next section (step {wizard_step_num + 1})",
                        selector=".btn-apply",  # Continue button selector
                        field_name="continue",
                        required=True,
                        metadata={
                            "platform": "linkedin",
                            "from_step": wizard_step_num,
                            "to_step": wizard_step_num + 1,
                        },
                    )
                    steps.append(continue_step)
                    step_num += 1
                    logger.info(
                        f"[LinkedInQuestionIntegrator] Inserted CONTINUE action after step {wizard_step_num}"
                    )
                elif wizard_step_num == max(fields_by_step.keys()):
                    # Add final CONTINUE to reach review/submit page (step 5)
                    continue_step = ExecutionPlanStep(
                        step_number=step_num,
                        action=ExecutionAction.CONTINUE_TO_NEXT_STEP,
                        description=f"Continue to review/submit page",
                        selector=".btn-apply",  # Continue button selector
                        field_name="continue",
                        required=True,
                        metadata={
                            "platform": "linkedin",
                            "from_step": wizard_step_num,
                            "to_step": wizard_step_num + 1,
                            "final_continue": True,
                        },
                    )
                    steps.append(continue_step)
                    step_num += 1
                    logger.info(
                        f"[LinkedInQuestionIntegrator] Inserted final CONTINUE action to reach review page"
                    )
        else:
            # No wizard steps detected - generate flat list
            logger.info(
                f"[LinkedInQuestionIntegrator] No wizard steps detected - generating flat list"
            )
            for question, category in classified:
                selector = question.selector
                field_type = question.field_type
                text = question.text

                if field_type == "file":
                    continue

                answer = answers.get(selector, "")

                # Determine action based on field type
                if field_type == "textarea":
                    action = ExecutionAction.FILL_PROFILE
                elif field_type in ("select", "radio", "checkbox"):
                    action = ExecutionAction.SELECT_OPTIONS
                else:
                    action = ExecutionAction.FILL_PROFILE

                step = ExecutionPlanStep(
                    step_number=step_num,
                    action=action,
                    description=f"Answer: {text}",
                    selector=selector,
                    field_name=question.label or text,
                    expected_value=answer,
                    value_source="mapped",
                    required=False,
                    metadata={
                        "platform": "linkedin",
                        "question_type": field_type,
                        "question_category": str(category),
                        "original_text": text,
                    },
                )

                steps.append(step)
                step_num += 1

        logger.info(
            f"[LinkedInQuestionIntegrator] Generated {len(steps)} execution steps "
            f"(includes CONTINUE actions for wizard navigation)"
        )

        return steps

    def _group_fields_by_wizard_step(self, questions: List[Question]) -> dict:
        """
        Group form fields by their parent wizard step div.

        Detects patterns like:
        <div id="step-1">
            <input id="first_name">
            <input id="last_name">
        </div>
        <div id="step-2">
            <select id="work_auth">
        </div>

        Returns:
            Dict mapping step number to list of questions in that step
            Example: {1: [q1, q2], 2: [q3, q4], 3: [q5]}
        """
        import re

        fields_by_step = {}

        # Check if any questions have metadata indicating step membership
        # This would come from parsing the HTML structure
        for question in questions:
            # Try to detect step from selector context
            # Pattern: fields inside <div id="step-N">
            step_num = self._detect_wizard_step_from_selector(question.selector)

            if step_num is not None:
                if step_num not in fields_by_step:
                    fields_by_step[step_num] = []
                fields_by_step[step_num].append(question)

        return fields_by_step if len(fields_by_step) > 1 else {}

    def _detect_wizard_step_from_selector(self, selector: str) -> Optional[int]:
        """
        Detect which wizard step a field belongs to based on its selector.

        Uses knowledge of common field groupings:
        - Step 1: first_name, last_name, email, phone
        - Step 2: work_auth, sponsorship
        - Step 3: experience, notice_period
        - Step 4: resume, cover_letter

        Returns step number (1-based) or None if not in a wizard step.
        """
        import re

        # Extract field ID/name from selector
        field_id = None
        if selector.startswith("#"):
            field_id = selector[1:]
        elif "name=" in selector:
            match = re.search(r'name="([^"]+)"', selector)
            if match:
                field_id = match.group(1)

        if not field_id:
            return None

        # Map fields to wizard steps based on common patterns
        step_1_fields = ["first_name", "last_name", "email", "phone"]
        step_2_fields = ["work_auth", "work_authorization", "sponsorship"]
        step_3_fields = ["experience", "notice_period"]
        step_4_fields = ["cover_letter"]  # resume handled separately

        if field_id in step_1_fields:
            return 1
        elif field_id in step_2_fields:
            return 2
        elif field_id in step_3_fields:
            return 3
        elif field_id in step_4_fields:
            return 4

        return None

    async def augment_execution_plan(
        self,
        plan: ExecutionPlan,
        page_html: str,
        insert_after_step: int = 1,
    ) -> ExecutionPlan:
        """
        Augment existing ExecutionPlan with detected questions.

        Inserts question steps into the plan at the specified position.
        Does NOT mutate the input plan - returns a new augmented plan.

        Args:
            plan: Existing ExecutionPlan (not mutated)
            page_html: LinkedIn page HTML
            insert_after_step: Insert question steps after this step number

        Returns:
            New augmented ExecutionPlan (input plan unchanged)
        """
        logger.info("[LinkedInQuestionIntegrator] Augmenting execution plan with questions")

        # Detect questions in page
        questions = await self.detect_linkedin_questions(page_html)

        if not questions:
            logger.info("[LinkedInQuestionIntegrator] No questions detected, returning copy of plan")
            # Return a new plan with same content (don't mutate input)
            from copy import deepcopy
            return deepcopy(plan)

        logger.info(f"[LinkedInQuestionIntegrator] Found {len(questions)} questions to integrate")

        # Generate question steps
        question_steps = await self.generate_question_steps(
            questions, start_step_number=insert_after_step + 1
        )

        # Create new plan with augmented steps (don't mutate input)
        from copy import deepcopy
        augmented_plan = deepcopy(plan)

        # Find insertion point in augmented plan
        insertion_index = 0
        for i, step in enumerate(augmented_plan.steps):
            if step.step_number >= insert_after_step:
                insertion_index = i + 1
                break

        # Insert question steps into new plan
        for question_step in reversed(question_steps):
            augmented_plan.steps.insert(insertion_index, question_step)

        # Renumber all steps
        for i, step in enumerate(augmented_plan.steps, start=1):
            step.step_number = i

        logger.info(
            f"[LinkedInQuestionIntegrator] Plan augmented: {len(augmented_plan.steps)} total steps"
        )

        return augmented_plan

    def get_integration_summary(
        self, questions: List[Question]
    ) -> str:
        """
        Get human-readable summary of question integration.

        Args:
            questions: Detected questions

        Returns:
            Summary string
        """
        if not questions:
            return "No questions detected"

        # Classify for summary
        classified = self.classify_linkedin_questions(questions)

        category_counts = {}
        for _, category in classified:
            cat_str = str(category).split(".")[-1]
            category_counts[cat_str] = category_counts.get(cat_str, 0) + 1

        lines = [
            f"LinkedIn Questions Detected: {len(questions)}",
            "",
            "By Category:",
        ]

        for category, count in sorted(category_counts.items()):
            lines.append(f"  - {category}: {count}")

        lines.extend(
            [
                "",
                "Questions:",
            ]
        )

        for question, category in classified:
            cat_str = str(category).split(".")[-1]
            text = question.text[:60]
            lines.append(f"  - [{cat_str}] {text}")

        return "\n".join(lines)


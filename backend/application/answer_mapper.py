"""
Answer Mapper

Maps question categories to default answers.
Supports future profile integration.
"""

from backend.application.question_classifier import QuestionCategory


class AnswerMapper:
    """Maps question categories to answers."""

    # Default answers for each category
    DEFAULT_ANSWERS = {
        QuestionCategory.WORK_AUTHORIZATION: "true",
        QuestionCategory.SPONSORSHIP: "false",
        QuestionCategory.EXPERIENCE: "5-10",
        QuestionCategory.SALARY: "50000",
        QuestionCategory.SALARY_PERIOD: "annual",
        QuestionCategory.NOTICE_PERIOD: "Immediate",
        QuestionCategory.RELOCATION: "true",
        QuestionCategory.REMOTE_WORK: "true",
        QuestionCategory.EDUCATION: "Bachelor",
        QuestionCategory.GENERIC: "",
    }

    def __init__(self, profile: dict = None):
        """
        Initialize answer mapper.

        Args:
            profile: Optional user profile with custom answers
        """
        self.profile = profile or {}
        self.answers = self.DEFAULT_ANSWERS.copy()

        # Override with profile values if provided
        if profile:
            self._load_profile_answers(profile)

    def _load_profile_answers(self, profile: dict):
        """Load answers from user profile."""
        # Future: Map profile fields to question categories
        if "years_of_experience" in profile:
            self.answers[QuestionCategory.EXPERIENCE] = profile["years_of_experience"]

        if "expected_salary" in profile:
            self.answers[QuestionCategory.SALARY] = profile["expected_salary"]

        if "education" in profile:
            self.answers[QuestionCategory.EDUCATION] = profile["education"]

    def get_answer(self, category: QuestionCategory) -> str:
        """
        Get answer for a category.

        Args:
            category: QuestionCategory

        Returns:
            Answer value
        """
        return self.answers.get(category, "")

    def get_answer_for_field_type(self, category: QuestionCategory, field_type: str, options: list = None) -> str:
        """
        Get answer formatted for field type.

        Args:
            category: QuestionCategory
            field_type: Field type (text, select, radio, checkbox, number)
            options: Available options for radio/select fields

        Returns:
            Formatted answer value
        """
        answer = self.get_answer(category)

        # For number inputs, extract first number from range answers like "5-10"
        if field_type == "number":
            # Handle range answers like "5-10" by extracting first number
            if "-" in answer and not answer.startswith("-"):
                # Split on dash and take first number
                parts = answer.split("-")
                if parts[0].strip().isdigit():
                    return parts[0].strip()
            # If already a valid number, return as-is
            if answer.isdigit():
                return answer
            # Fallback: try to extract any digits
            import re
            match = re.search(r'\d+', answer)
            if match:
                return match.group(0)
            # Last resort: return "0"
            return "0"

        # For radio buttons, map answer to actual option value
        if field_type == "radio" and options:
            # Map category answers to preferred option patterns
            category_patterns = {
                QuestionCategory.WORK_AUTHORIZATION: ["yes", "authorized", "true", "1"],
                QuestionCategory.SPONSORSHIP: ["no", "false", "0", "none"],
                QuestionCategory.RELOCATION: ["yes", "true", "1", "willing"],
                QuestionCategory.REMOTE_WORK: ["yes", "true", "1", "prefer"],
                QuestionCategory.NOTICE_PERIOD: ["immediate", "now", "asap"],
            }

            # Get preferred values for this category
            preferred = category_patterns.get(category, [])

            # Find first matching option (case-insensitive)
            for pref in preferred:
                for option in options:
                    if option.lower() == pref.lower():
                        return option

            # If no match, use first option as fallback
            if options:
                return options[0]
            return ""

        # For select dropdowns with options (like salary period)
        if field_type == "select" and options:
            # Map categories to preferred option patterns
            category_patterns = {
                QuestionCategory.SALARY_PERIOD: ["annual", "yearly", "year"],
                QuestionCategory.NOTICE_PERIOD: ["immediate", "now", "asap"],
            }

            # Get preferred values for this category
            preferred = category_patterns.get(category, [])

            if preferred:
                # Find first matching option (case-insensitive)
                for pref in preferred:
                    for option in options:
                        if option.lower() == pref.lower():
                            return option

            # If no match, use first option as fallback
            if options:
                return options[0]
            return ""

        # Format for checkboxes (true/false mapping)
        if field_type == "checkbox":
            if answer.lower() in ("true", "yes", "1"):
                return "true"
            elif answer.lower() in ("false", "no", "0"):
                return "false"

        return answer

    def map_questions_to_answers(self, classified_questions: dict) -> dict:
        """
        Map classified questions to answers.

        Args:
            classified_questions: Output from QuestionClassifier.classify_multiple()

        Returns:
            Dictionary mapping selectors to answers
        """
        results = {}

        for selector, question_info in classified_questions.items():
            category = question_info["category"]
            field_type = question_info["field_type"]
            options = question_info.get("options")

            # Pass options to get_answer_for_field_type for radio button handling
            answer = self.get_answer_for_field_type(category, field_type, options)

            results[selector] = {
                "text": question_info["text"],
                "category": category,
                "field_type": field_type,
                "answer": answer,
                "options": options,
            }

        return results

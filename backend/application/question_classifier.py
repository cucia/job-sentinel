"""
Question Classifier

Classifies detected questions into answer categories.
Uses rule-based classification without AI dependencies.
"""

from enum import Enum
from typing import Optional
import re


class QuestionCategory(str, Enum):
    """Question categories for answer mapping."""
    WORK_AUTHORIZATION = "work_authorization"
    SPONSORSHIP = "sponsorship"
    EXPERIENCE = "experience"
    SALARY = "salary"
    SALARY_PERIOD = "salary_period"
    NOTICE_PERIOD = "notice_period"
    RELOCATION = "relocation"
    REMOTE_WORK = "remote_work"
    EDUCATION = "education"
    GENERIC = "generic"


class QuestionClassifier:
    """Classifies questions by category."""

    # Classification rules (keyword patterns)
    RULES = {
        QuestionCategory.WORK_AUTHORIZATION: [
            r"legally authorized",
            r"work authorization",
            r"authorized to work",
            r"legal right to work",
            r"visa status",
            r"work auth",
            r"authorization",
        ],
        QuestionCategory.SPONSORSHIP: [
            r"visa sponsorship",
            r"require sponsorship",
            r"sponsorship needed",
            r"require visa",
            r"sponsorship",
            r"sponsor",
        ],
        QuestionCategory.EXPERIENCE: [
            r"years of experience",
            r"years experience",
            r"experience level",
            r"relevant experience",
            r"how many years",
            r"years in",
            r"experience",
        ],
        QuestionCategory.SALARY: [
            r"expected salary",
            r"current salary",
            r"salary expectation",
            r"salary range",
            r"compensation",
            r"salary amount",
            r"salary$",  # Match "salary" at end of phrase (not "salary period")
        ],
        QuestionCategory.SALARY_PERIOD: [
            r"salary period",
            r"pay frequency",
            r"compensation period",
            r"payment period",
            r"pay period",
            r"period$",  # Match "period" at end of phrase
        ],
        QuestionCategory.NOTICE_PERIOD: [
            r"notice period",
            r"available to join",
            r"when can you start",
            r"joining availability",
            r"notice",
        ],
        QuestionCategory.RELOCATION: [
            r"willing to relocate",
            r"relocate",
            r"relocation",
            r"move to",
            r"willing to move",
        ],
        QuestionCategory.REMOTE_WORK: [
            r"remote work",
            r"work from home",
            r"wfh",
            r"remote preference",
            r"remote position",
            r"remote",
            r"prefer remote",
        ],
        QuestionCategory.EDUCATION: [
            r"degree",
            r"qualification",
            r"education",
            r"school",
            r"university",
            r"college",
        ],
    }

    def classify(self, question_text: str) -> QuestionCategory:
        """
        Classify a question by its text.

        Args:
            question_text: The question text to classify

        Returns:
            QuestionCategory
        """
        text_lower = question_text.lower()

        # Check each category's rules
        for category, patterns in self.RULES.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return category

        # Default to generic
        return QuestionCategory.GENERIC

    def classify_multiple(self, questions) -> dict:
        """
        Classify multiple questions.

        Args:
            questions: List of Question objects

        Returns:
            Dictionary mapping questions to categories
        """
        results = {}
        for question in questions:
            results[question.selector] = {
                "text": question.text,
                "category": self.classify(question.text),
                "field_type": question.field_type,
                "options": question.options,
            }
        return results

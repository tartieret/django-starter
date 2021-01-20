from typing import Dict, List

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .question import Question


class OpenAnswerType:
    NUMBER = "number"
    STRING = "string"


class OpenQuestion(Question):
    """Open question"""

    TYPES = (
        (OpenAnswerType.NUMBER, _("Number")),
        (OpenAnswerType.STRING, _("String")),
    )

    answer = models.CharField(
        max_length=50, help_text=_("Answer to the question"), verbose_name=_("Answer")
    )

    answer_type = models.CharField(
        max_length=8,
        choices=TYPES,
        verbose_name=_("Type"),
        help_text=_("Type of the expected answer"),
        default=OpenAnswerType.NUMBER,
    )

    def check_if_correct(self, guess: str) -> bool:
        try:
            if self.answer_type == OpenAnswerType.NUMBER:
                user_guess = float(guess)
                expected_answer = float(self.answer)
                return user_guess == expected_answer
            else:
                user_guess = guess.strip().lower()
                expected_answer = guess.strip().lower()
                return user_guess == expected_answer
        except:
            return False

    def get_answers(self) -> List[Dict]:
        return [
            {"correct": True, "content": self.answer},
        ]

    def get_answers_list(self):
        return False

    def answer_choice_to_string(self, guess):
        return str(guess)

    class Meta:
        verbose_name = _("Open Question")
        verbose_name_plural = _("Open Questions")
        # ordering = ["id"]

    def clean(self):
        try:
            if self.answer_type == OpenAnswerType.NUMBER:
                # check if the expected answer is a proper number
                expected_answer = float(self.answer)
        except:
            raise ValidationError({"answer": _("This is not a valid number")})

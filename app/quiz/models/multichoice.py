from django.db import models
from django.utils.translation import gettext_lazy as _

from .question import Question

ANSWER_ORDER_OPTIONS = (
    ("content", _("Content")),
    ("random", _("Random")),
    ("none", _("None")),
)


class MCQuestion(Question):

    answer_order = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        choices=ANSWER_ORDER_OPTIONS,
        help_text=_(
            "The order in which multichoice "
            "answer options are displayed "
            "to the user"
        ),
        verbose_name=_("Answer Order"),
    )

    allow_multiple_answers = models.BooleanField(
        verbose_name=_("Allow several answers"),
        default=False,
        help_text=_("If true, the user can select several answers"),
    )

    def check_if_correct(self, guess):
        if self.allow_multiple_answers:
            answers = Answer.objects.filter(id__in=guess)
        else:
            answers = [Answer.objects.get(id=guess)]

        for answer in answers:
            if not answer.correct:
                return False

        return True

    def order_answers(self, queryset):
        if self.answer_order == "content":
            return queryset.order_by("content")
        if self.answer_order == "random":
            return queryset.order_by("?")
        if self.answer_order == "none":
            return queryset.order_by()
        return queryset

    def get_answers(self):
        return self.order_answers(Answer.objects.filter(question=self))

    def get_answers_list(self):
        return [
            (answer.id, answer.content)
            for answer in self.order_answers(Answer.objects.filter(question=self))
        ]

    def answer_choice_to_string(self, guess):
        return Answer.objects.get(id=guess).content

    class Meta:
        verbose_name = _("Multiple Choice Question")
        verbose_name_plural = _("Multiple Choice Questions")


class Answer(models.Model):
    question = models.ForeignKey(
        MCQuestion, verbose_name=_("Question"), on_delete=models.CASCADE
    )

    content = models.CharField(
        max_length=1000,
        blank=False,
        help_text=_("Enter the answer text that " "you want displayed"),
        verbose_name=_("Content"),
    )

    correct = models.BooleanField(
        blank=False,
        default=False,
        help_text=_("Is this a correct answer?"),
        verbose_name=_("Correct"),
    )

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")

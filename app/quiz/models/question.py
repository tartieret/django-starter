from django.db import models
from django.utils.translation import gettext_lazy as _

from model_utils.managers import InheritanceManager

from .category import Category, SubCategory
from .quiz import Quiz


class Question(models.Model):
    """
    Base class for all question types.
    Shared properties placed here.
    """

    quiz = models.ManyToManyField(Quiz, verbose_name=_("Quiz"), blank=True)

    category = models.ManyToManyField(
        Category, verbose_name=_("Category"), blank=True, related_name="questions"
    )

    content = models.TextField(
        max_length=1000,
        blank=False,
        help_text=_("Enter the question text that " "you want displayed"),
        verbose_name=_("Question"),
    )

    explanation = models.TextField(
        max_length=2000,
        blank=True,
        help_text=_(
            "Explanation to be shown " "after the question has " "been answered."
        ),
        verbose_name=_("Explanation"),
    )

    objects = InheritanceManager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["content"]

    def __str__(self):
        return self.content

    def type(self):
        return self.__class__.__name__

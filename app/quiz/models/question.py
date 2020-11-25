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

    category = models.ForeignKey(
        Category,
        verbose_name=_("Category"),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    sub_category = models.ForeignKey(
        SubCategory,
        verbose_name=_("Sub-Category"),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    figure = models.ImageField(
        upload_to="uploads/%Y/%m/%d", blank=True, null=True, verbose_name=_("Figure")
    )

    content = models.CharField(
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
        ordering = ["category"]

    def __str__(self):
        return self.content

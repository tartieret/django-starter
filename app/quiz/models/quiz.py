import re

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .category import Category


class QuizType:
    GENERAL = "general"
    TOPIC = "topic"
    MONTHLY = "monthly"

    @staticmethod
    def is_valid(value):
        return value in [QuizType.GENERAL, QuizType.TOPIC, QuizType.MONTHLY]


class Quiz(models.Model):

    TYPES = (
        (QuizType.GENERAL, _("General")),
        (QuizType.TOPIC, _("Topic")),
        (QuizType.MONTHLY, _("Monthly")),
    )

    title = models.CharField(verbose_name=_("Title"), max_length=60, blank=False)

    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        help_text=_("a description of the quiz"),
    )

    type = models.CharField(
        _("Type"), max_length=10, choices=TYPES, default=QuizType.GENERAL
    )

    url = models.SlugField(
        max_length=60,
        blank=False,
        help_text=_("a user friendly url"),
        verbose_name=_("user friendly url"),
    )

    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        verbose_name=_("Category"),
        on_delete=models.CASCADE,
    )

    random_order = models.BooleanField(
        blank=False,
        default=False,
        verbose_name=_("Random Order"),
        help_text=_(
            "Display the questions in " "a random order or as they " "are set?"
        ),
    )

    max_questions = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Max Questions"),
        help_text=_("Number of questions to be answered on each attempt."),
    )

    exam_paper = models.BooleanField(
        blank=False,
        default=False,
        help_text=_(
            "If yes, the result of each"
            " attempt by a user will be"
            " stored. Necessary for marking."
        ),
        verbose_name=_("Exam Paper"),
    )

    single_attempt = models.BooleanField(
        blank=False,
        default=False,
        help_text=_(
            "If yes, only one attempt by"
            " a user will be permitted."
            " Non users cannot sit this exam."
        ),
        verbose_name=_("Single Attempt"),
    )

    pass_mark = models.SmallIntegerField(
        blank=True,
        default=0,
        verbose_name=_("Pass Mark"),
        help_text=_("Percentage required to pass exam."),
        validators=[MaxValueValidator(100)],
    )

    success_text = models.TextField(
        blank=True,
        help_text=_("Displayed if user passes."),
        verbose_name=_("Success Text"),
    )

    fail_text = models.TextField(
        verbose_name=_("Fail Text"), blank=True, help_text=_("Displayed if user fails.")
    )

    draft = models.BooleanField(
        blank=True,
        default=False,
        verbose_name=_("Draft"),
        help_text=_(
            "If yes, the quiz is not displayed"
            " in the quiz list and can only be"
            " taken by users who can edit"
            " quizzes."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, help_text=_("Date of creation")
    )

    updated_at = models.DateTimeField(auto_now=True, help_text=_("Date of last update"))

    def clean(self):
        if self.type == QuizType.TOPIC and self.category is None:
            raise ValidationError(
                {"category": _('A "topic" quiz should have a category')}
            )

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.url = re.sub(r"\s+", "-", self.url).lower()

        self.url = "".join(
            letter for letter in self.url if letter.isalnum() or letter == "-"
        )

        if self.single_attempt is True:
            self.exam_paper = True

        if self.pass_mark > 100:
            raise ValidationError("%s is above 100" % self.pass_mark)

        super(Quiz, self).save(force_insert, force_update, *args, **kwargs)

    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.question_set.all().select_subclasses()

    @property
    def get_max_score(self):
        return self.get_questions().count()

    def anon_score_id(self):
        return str(self.id) + "_score"

    def anon_q_list(self):
        return str(self.id) + "_q_list"

    def anon_q_data(self):
        return str(self.id) + "_data"

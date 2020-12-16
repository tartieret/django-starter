import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import (
    validate_comma_separated_integer_list,
)
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from .quiz import Quiz
from .question import Question


class SittingMode:
    STUDY = "study"
    EXAM = "exam"

    @staticmethod
    def is_valid(value):
        return value in [SittingMode.STUDY, SittingMode.EXAM]


class SittingManager(models.Manager):
    def new_sitting(self, user, quiz, mode=SittingMode.STUDY):
        if quiz.random_order is True:
            question_set = quiz.question_set.all().select_subclasses().order_by("?")
        else:
            question_set = quiz.question_set.all().select_subclasses()

        if quiz.max_questions and quiz.max_questions < question_set.count():
            question_set = question_set[: quiz.max_questions]

        if len(question_set) == 0:
            raise ImproperlyConfigured(
                "This quiz does not contain any question. "
                "Please configure questions properly"
            )

        question_ids = [item.id for item in question_set]
        questions = ",".join(map(str, question_ids)) + ","

        user_progress = {order: "?" for order in range(1, len(question_ids) + 1)}

        new_sitting = self.create(
            user=user,
            quiz=quiz,
            mode=mode,
            question_order=questions,
            # question_list=questions,
            # incorrect_questions="",
            current_score=0,
            complete=False,
            user_answers=json.dumps(user_progress),
        )

        # generate default user answers
        UserAnswer.objects.bulk_create(
            [
                UserAnswer(
                    question=question, user=user, sitting=new_sitting, order=i + 1
                )
                for i, question in enumerate(question_set)
            ]
        )

        return new_sitting

    def user_sitting(self, user, quiz, mode=SittingMode.STUDY):
        """Retrieve an existing sitting for the current quiz
        or start a new one
        """
        if (
            quiz.single_attempt is True
            and self.filter(user=user, quiz=quiz, mode=mode, complete=True).exists()
        ):
            return False

        try:
            sitting = self.get(user=user, quiz=quiz, mode=mode, complete=False)
        except Sitting.DoesNotExist:
            sitting = self.new_sitting(user, quiz, mode=mode)
        except Sitting.MultipleObjectsReturned:
            sitting = self.filter(user=user, quiz=quiz, mode=mode, complete=False)[0]
        return sitting


class Sitting(models.Model):
    """
    Used to store the progress of logged in users sitting a quiz.
    Replaces the session system used by anon users.

    Question_order is a list of integer pks of all the questions in the
    quiz, in order.

    Question_list is a list of integers which represent id's of
    the unanswered questions in csv format.

    Sitting deleted when quiz finished unless quiz.exam_paper is true.

    User_answers is a json object in which the question order id is stored
    with 0 or 1 based on the fact that the user was correct or not
    """

    MODES = ((SittingMode.STUDY, _("Study")), (SittingMode.EXAM, _("Exam")))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE
    )

    quiz = models.ForeignKey(Quiz, verbose_name=_("Quiz"), on_delete=models.CASCADE)

    mode = models.CharField(_("Mode"), max_length=10, choices=MODES, default="study")

    question_order = models.CharField(
        max_length=1024,
        verbose_name=_("Question Order"),
        validators=[validate_comma_separated_integer_list],
    )

    # question_list = models.CharField(
    #     max_length=1024,
    #     verbose_name=_("Question List"),
    #     validators=[validate_comma_separated_integer_list],
    # )

    # incorrect_questions = models.CharField(
    #     max_length=1024,
    #     blank=True,
    #     verbose_name=_("Incorrect questions"),
    #     validators=[validate_comma_separated_integer_list],
    # )

    current_score = models.IntegerField(verbose_name=_("Current Score"))

    complete = models.BooleanField(
        default=False, blank=False, verbose_name=_("Complete")
    )

    user_answers = models.TextField(
        blank=True, default="{}", verbose_name=_("User Answers")
    )

    start = models.DateTimeField(auto_now_add=True, verbose_name=_("Start"))

    end = models.DateTimeField(null=True, blank=True, verbose_name=_("End"))

    objects = SittingManager()

    class Meta:
        permissions = (("view_sittings", _("Can see completed exams.")),)

    def add_to_score(self, points):
        self.current_score += int(points)

    @property
    def get_current_score(self):
        return self.current_score

    def _question_ids(self):
        return [int(n) for n in self.question_order.split(",") if n]

    @property
    def get_percent_correct(self):
        dividend = float(self.current_score)
        divisor = len(self._question_ids())
        if divisor < 1:
            return 0  # prevent divide by zero error

        if dividend > divisor:
            return 100

        correct = int(round((dividend / divisor) * 100))

        if correct >= 1:
            return correct
        else:
            return 0

    def mark_quiz_complete(self):
        self.complete = True
        self.end = now()

    # def add_incorrect_question(self, question):
    #     """
    #     Adds uid of incorrect question to the list.
    #     The question object must be passed in.
    #     """
    #     if len(self.incorrect_questions) > 0:
    #         self.incorrect_questions += ","
    #     self.incorrect_questions += str(question.id) + ","
    #     if self.complete:
    #         self.add_to_score(-1)
    #     self.save()

    # @property
    # def get_incorrect_questions(self):
    #     """
    #     Returns a list of non empty integers, representing the pk of
    #     questions
    #     """
    #     return [int(q) for q in self.incorrect_questions.split(",") if q]

    # def remove_incorrect_question(self, question):
    #     current = self.get_incorrect_questions
    #     current.remove(question.id)
    #     self.incorrect_questions = ",".join(map(str, current))
    #     self.add_to_score(1)
    #     self.save()

    @property
    def check_if_passed(self):
        return self.get_percent_correct >= self.quiz.pass_mark

    @property
    def result_message(self):
        if self.check_if_passed:
            return self.quiz.success_text
        else:
            return self.quiz.fail_text

    def add_user_progress(self, question_order, is_correct):
        current = json.loads(self.user_answers)
        current[question_order] = 1 if is_correct else 0
        self.user_answers = json.dumps(current)

    # def get_questions(self, with_answers=False):
    #     question_ids = self._question_ids()
    #     questions = sorted(
    #         self.quiz.question_set.filter(id__in=question_ids).select_subclasses(),
    #         key=lambda q: question_ids.index(q.id),
    #     )

    #     if with_answers:
    #         user_answers = json.loads(self.user_answers)
    #         for question in questions:
    #             question.user_answer = user_answers[str(question.id)]

    #     return questions

    # @property
    # def questions_with_user_answers(self):
    #     return {q: q.user_answer for q in self.get_questions(with_answers=True)}

    @property
    def get_max_score(self):
        return len(self._question_ids())

    def progress(self):
        """
        Returns the number of questions answered so far and the total number of
        questions.
        """
        answers = json.loads(self.user_answers)
        answered = len([i for i, answer in answers.items() if answer != "?"])
        print("Answered: ", answered)
        total = self.get_max_score
        return answered, total

    def get_nb_questions(self) -> int:
        return len(self._question_ids())

    def get_unanswered_questions(self) -> list:
        """Return the list of unanswered questions
        
        Returns:
            list: all question order ids that don't have an answer
        
        """
        answers = json.loads(self.user_answers)
        unanswered = [i for i, answer in answers.items() if answer == "?"]
        return unanswered

    def get_nb_unanswered_questions(self) -> int:
        """Get the number of unanswered questions
        
        Returns:
            int: number of unanswered questions
        
        """
        unanswered = self.get_unanswered_questions()
        return len(unanswered)


    def get_score_list(self) -> list:
        """Return a list of 0,1,? based on the fact that
        user answers are correct or not"""
        answers = json.loads(self.user_answers)
        return [(i, answer) for i, answer in answers.items()]


class UserAnswer(models.Model):

    sitting = models.ForeignKey(
        "Sitting",
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("Sitting"),
        help_text=_("Sitting this answer is linked to"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("User"),
        help_text=_("User that generated this answer"),
    )

    order = models.PositiveIntegerField(
        verbose_name=_("Order of the question in the sitting")
    )

    question = models.ForeignKey(
        "Question",
        on_delete=models.CASCADE,
        verbose_name=_("Question"),
        help_text=_("question the user answered to"),
    )

    answer = models.CharField(
        max_length=50,
        verbose_name=_("User answer"),
        default=None,
        null=True,
        blank=True,
    )

    is_correct = models.BooleanField(
        verbose_name=_("Is correct"), null=True, default=None
    )

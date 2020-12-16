from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    DetailView,
    ListView,
    TemplateView,
    FormView,
    RedirectView,
)

from .forms import MCQuestionForm, EssayForm
from .models import (
    Category,
    Essay_Question,
    Progress,
    Question,
    Quiz,
    Sitting,
    SittingMode,
    UserAnswer,
)


class QuizMarkerMixin:
    @method_decorator(login_required)
    @method_decorator(permission_required("quiz.view_sittings"))
    def dispatch(self, *args, **kwargs):
        return super(QuizMarkerMixin, self).dispatch(*args, **kwargs)


class SittingFilterTitleMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        quiz_filter = self.request.GET.get("quiz_filter")
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)

        return queryset


class QuizListView(LoginRequiredMixin, ListView):
    model = Quiz

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(draft=False)


class QuizDetailView(LoginRequiredMixin, DetailView):
    model = Quiz
    slug_field = "url"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.draft and not request.user.has_perm("quiz.change_quiz"):
            raise PermissionDenied

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class CategoriesListView(LoginRequiredMixin, ListView):
    model = Category


class ViewQuizListByCategory(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = "view_quiz_category.html"

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category, category=self.kwargs["category_name"]
        )

        return super(ViewQuizListByCategory, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewQuizListByCategory, self).get_context_data(**kwargs)

        context["category"] = self.category
        return context

    def get_queryset(self):
        queryset = super(ViewQuizListByCategory, self).get_queryset()
        return queryset.filter(category=self.category, draft=False)


class QuizUserProgressView(LoginRequiredMixin, TemplateView):
    template_name = "progress.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(QuizUserProgressView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuizUserProgressView, self).get_context_data(**kwargs)
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        context["cat_scores"] = progress.list_all_cat_scores
        context["exams"] = progress.show_exams()
        return context


class QuizMarkingList(
    LoginRequiredMixin, QuizMarkerMixin, SittingFilterTitleMixin, ListView
):
    model = Sitting

    def get_queryset(self):
        queryset = super(QuizMarkingList, self).get_queryset().filter(complete=True)

        user_filter = self.request.GET.get("user_filter")
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)

        return queryset


class QuizMarkingDetail(LoginRequiredMixin, QuizMarkerMixin, DetailView):
    model = Sitting

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()

        q_to_toggle = request.POST.get("qid", None)
        if q_to_toggle:
            q = Question.objects.get_subclass(id=int(q_to_toggle))
            if int(q_to_toggle) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(q)
            else:
                sitting.add_incorrect_question(q)

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
        context["questions"] = context["sitting"].get_questions(with_answers=True)
        return context


# class QuizStart(LoginRequiredMixin, FormView):
#     form_class = QuestionForm
#     # template_name = "question.html"
#     # result_template_name = "result.html"
#     # single_complete_template_name = "single_complete.html"

#     def dispatch(self, request, *args, **kwargs):
#         self.quiz = get_object_or_404(Quiz, url=self.kwargs["quiz_name"])

#         # find out if it's study or exam mode
#         self.mode = request.GET.get("mode", SittingMode.STUDY)
#         if not SittingMode.is_valid(self.mode):
#             raise Http404

#         if self.quiz.draft and not request.user.has_perm("quiz.change_quiz"):
#             raise PermissionDenied

#         self.sitting = Sitting.objects.user_sitting(request.user, self.quiz, self.mode)

#         if not self.sitting:
#             return render(request, self.single_complete_template_name)

#         return super().dispatch(request, *args, **kwargs)

#     def get_form(self, *args, **kwargs):
#         self.question = self.sitting.get_first_question()
#         self.progress = self.sitting.progress()

#         if self.question.__class__ is Essay_Question:
#             form_class = EssayForm
#         else:
#             form_class = self.form_class

#         return form_class(**self.get_form_kwargs())

#     def get_form_kwargs(self):
#         kwargs = super(QuizTake, self).get_form_kwargs()
#         return dict(kwargs, question=self.question)

#     def form_valid(self, form):
#         self.form_valid_user(form)
#         if self.sitting.get_first_question() is False:
#             return self.final_result_user()

#         self.request.POST = {}
#         return super().get(self, self.request)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["question"] = self.question
#         context["quiz"] = self.quiz
#         if hasattr(self, "previous"):
#             context["previous"] = self.previous
#         if hasattr(self, "progress"):
#             context["progress"] = self.progress
#         return context

#     def form_valid_user(self, form):
#         progress, c = Progress.objects.get_or_create(user=self.request.user)
#         guess = form.cleaned_data["answers"]
#         is_correct = self.question.check_if_correct(guess)

#         if is_correct is True:
#             self.sitting.add_to_score(1)
#             progress.update_score(self.question, 1, 1)
#         else:
#             self.sitting.add_incorrect_question(self.question)
#             progress.update_score(self.question, 0, 1)

#         if self.sitting.mode == SittingMode.STUDY:
#             # in study mode, we show the answer to the previous question
#             self.previous = {
#                 "previous_answer": guess,
#                 "previous_outcome": is_correct,
#                 "previous_question": self.question,
#                 "answers": self.question.get_answers(),
#                 "question_type": {self.question.__class__.__name__: True},
#             }
#         else:
#             self.previous = {}

#         self.sitting.add_user_answer(self.question, guess)
#         self.sitting.remove_first_question()

#     # def final_result_user(self):
#     #     results = {
#     #         "quiz": self.quiz,
#     #         "score": self.sitting.get_current_score,
#     #         "max_score": self.sitting.get_max_score,
#     #         "percent": self.sitting.get_percent_correct,
#     #         "sitting": self.sitting,
#     #         "previous": self.previous,
#     #     }

#     #     self.sitting.mark_quiz_complete()

#     #     if self.sitting.mode == SittingMode.EXAM:
#     #         results["questions"] = self.sitting.get_questions(with_answers=True)
#     #         results["incorrect_questions"] = self.sitting.get_incorrect_questions

#     #     if self.quiz.exam_paper is False:
#     #         self.sitting.delete()

#     #     results["mode"] = self.sitting.mode
#     #     return render(self.request, self.result_template_name, results)


class QuizStart(LoginRequiredMixin, RedirectView):
    """Start a new sitting and redirect to the first question"""

    permanent = False

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, url=self.kwargs["quiz_name"])
        # find out if it's study or exam mode
        self.mode = request.GET.get("mode", SittingMode.STUDY)
        if not SittingMode.is_valid(self.mode):
            raise Http404

        if self.quiz.draft and not request.user.has_perm("quiz.change_quiz"):
            raise PermissionDenied

        self.sitting = Sitting.objects.user_sitting(request.user, self.quiz, self.mode)

        if not self.sitting:
            return render(request, self.single_complete_template_name)

        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        url = reverse("quiz:sitting_question", args=[self.sitting.id, 1])
        return url


class SittingList(LoginRequiredMixin, ListView):
    model = Sitting

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)


class SittingQuestion(LoginRequiredMixin, FormView):
    template_name = "sitting_question.html"

    def dispatch(self, request, *args, **kwargs):
        sitting_id = self.kwargs.get("sitting_id")
        question_order = self.kwargs.get("question_order")

        # before selecting the user, check if authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # retrieve the current sitting
        self.sitting = get_object_or_404(Sitting, user=request.user, pk=sitting_id)
        self.mode = self.sitting.mode
        # retrieve the current question
        question_order = self.kwargs.get("question_order")
        self.user_answer = get_object_or_404(
            UserAnswer, user=request.user, sitting=sitting_id, order=question_order
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        self.question = Question.objects.get_subclass(pk=self.user_answer.question_id)
        if isinstance(self.question, Essay_Question):
            form_class = EssayForm
        else:
            form_class = MCQuestionForm
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return dict(kwargs, question=self.question)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sitting"] = self.sitting
        context["question"] = self.question
        context["user_answer"] = self.user_answer
        context["quiz"] = self.sitting.quiz
        context["question_type"]: {self.question.__class__.__name__: True}
        context["active_tab"] = "question"
        context["actual_answers"] = self.question.get_answers()
        context["nb_questions"] = self.sitting.get_nb_questions()
        return context

    def form_valid(self, form):
        # check the user answer
        self.validate_answer(form)
        if self.sitting.mode == SittingMode.STUDY:
            # stay on the same question and show the result
            self.request.POST = {}
            return super().get(self, self.request)
        else:
            # redirect to the next question
            url = reverse(
                "quiz:sitting_question",
                args=[self.sitting.id, self.user_answer.order + 1],
            )
            return HttpResponseRedirect(url)

    def validate_answer(self, form):
        self.user_answer.answer = form.cleaned_data["answers"]
        is_correct = self.question.check_if_correct(self.user_answer.answer)

        if is_correct is True:
            self.sitting.add_to_score(1)
            self.user_answer.is_correct = True
            # progress.update_score(self.question, 1, 1)
        else:
            self.sitting.add_incorrect_question(self.question)
            # progress.update_score(self.question, 0, 1)
            self.user_answer.is_correct = False

        self.user_answer.save()

    def get_success_url(self):
        if self.sitting.mode == SittingMode.STUDY:
            # stay on the same question and show the result
            url = reverse(
                "quiz:sitting_question", args=[self.sitting.id, self.user_answer.order]
            )
        else:
            # redirect to the next question
            url = reverse(
                "quiz:sitting_question",
                args=[self.sitting.id, self.user_answer.order + 1],
            )
        return url


class SittingQuestionExplanation(LoginRequiredMixin, TemplateView):
    template_name = "sitting_question_explanation.html"

    def get_context_data(self, **kwargs):
        sitting_id = self.kwargs.get("sitting_id")
        question_order = self.kwargs.get("question_order")
        # retrieve the current sitting
        self.sitting = get_object_or_404(Sitting, user=self.request.user, pk=sitting_id)
        self.mode = self.sitting.mode
        # retrieve the current question
        question_order = self.kwargs.get("question_order")
        self.user_answer = get_object_or_404(
            UserAnswer, user=self.request.user, sitting=sitting_id, order=question_order
        )
        self.question = Question.objects.get_subclass(pk=self.user_answer.question_id)

        context = super().get_context_data(**kwargs)
        context["question"] = self.question
        context["sitting"] = self.sitting
        context["user_answer"] = self.user_answer
        context["quiz"] = self.sitting.quiz
        context["active_tab"] = "explanation"
        context["nb_questions"] = self.sitting.get_nb_questions()
        return context

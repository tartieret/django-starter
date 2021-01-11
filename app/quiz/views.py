import json

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (
    DeleteView,
    DetailView,
    FormView,
    ListView,
    RedirectView,
    TemplateView,
    View,
)
from django.views.generic.detail import SingleObjectMixin

from .forms import EssayForm, MCQuestionForm, OpenQuestionForm
from .models import (
    Category,
    EssayQuestion,
    OpenQuestion,
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
        self.category = get_object_or_404(Category, name=self.kwargs["category_name"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["category"] = self.category
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
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


# class QuizMarkingDetail(LoginRequiredMixin, QuizMarkerMixin, DetailView):
#     model = Sitting

#     def post(self, request, *args, **kwargs):
#         sitting = self.get_object()

#         q_to_toggle = request.POST.get("qid", None)
#         if q_to_toggle:
#             q = Question.objects.get_subclass(id=int(q_to_toggle))
#             if int(q_to_toggle) in sitting.get_incorrect_questions:
#                 sitting.remove_incorrect_question(q)
#             else:
#                 sitting.add_incorrect_question(q)

#         return self.get(request)

#     def get_context_data(self, **kwargs):
#         context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
#         context["questions"] = context["sitting"].get_questions(with_answers=True)
#         return context


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


class SittingDelete(LoginRequiredMixin, DeleteView):
    model = Sitting
    pk_url_kwarg = "sitting_id"
    success_url = reverse_lazy("quiz:quiz_category_list_all")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)


class SittingList(LoginRequiredMixin, ListView):
    model = Sitting

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)


class SittingFinish(LoginRequiredMixin, SingleObjectMixin, View):

    pk_url_kwarg = "sitting_id"
    model = Sitting

    def get_queryset(self):
        """Restrict the list of sittings to the ones belonging to the current user"""
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user, complete=False)
        return queryset

    def post(self, request, *args, **kwargs):
        """On POST, mark the sitting as complete"""
        sitting = self.get_object()
        unanswered_questions = sitting.get_unanswered_questions()
        if len(unanswered_questions) > 0:
            # invalid, go back to unanswered questions
            url = reverse(
                "quiz:sitting_question",
                args=[sitting.id, unanswered_questions[0]],
            )
            return HttpResponseRedirect(url)
        else:
            sitting.mark_quiz_complete()
            sitting.save()
            url = reverse(
                "quiz:sitting_results",
                args=[sitting.id],
            )
            return HttpResponseRedirect(url)


class SittingResults(LoginRequiredMixin, DetailView):
    """Show the results for a given sitting"""

    template_name = "result.html"
    pk_url_kwarg = "sitting_id"
    model = Sitting

    def post(self, request, *args, **kwargs):
        """On POST, mark the sitting as complete"""
        self.object = self.get_object()
        unanswered_questions = self.object.get_unanswered_questions()
        if len(unanswered_questions) > 0:
            # invalid, go back to unanswered questions
            url = reverse(
                "quiz:sitting_question",
                args=[self.object.id, unanswered_questions[0]],
            )
            return HttpResponseRedirect(url)
        else:
            self.object.mark_quiz_complete()
            self.object.save()
            request.POST = {}
            return super().get(self, request)

    def get_queryset(self):
        """Restrict the list of sittings to the ones belonging to the current user"""
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user, complete=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = {
            **context,
            "quiz": self.object.quiz,
            "score": self.object.get_current_score,
            "max_score": self.object.get_max_score,
            "percent": self.object.get_percent_correct,
            "sitting": self.object,
        }
        return context


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
        if isinstance(self.question, EssayQuestion):
            form_class = EssayForm
        elif isinstance(self.question, OpenQuestion):
            form_class = OpenQuestionForm
        else:
            form_class = MCQuestionForm
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.user_answer.answer:
            selected_answers = str(self.user_answer.answer)
        else:
            selected_answers = None
        return dict(
            kwargs,
            question=self.question,
            selected_answers=selected_answers,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sitting"] = self.sitting
        context["question"] = self.question
        context["score_list"] = self.sitting.get_score_list()
        context["user_answer"] = self.user_answer
        context["quiz"] = self.sitting.quiz
        context["question_type"] = self.question.__class__.__name__
        context["active_tab"] = "question"
        context["actual_answers"] = self.question.get_answers()
        context["nb_questions"] = self.sitting.get_nb_questions()
        context["nb_unanswered_questions"] = self.sitting.get_nb_unanswered_questions()
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
            nb_questions = self.sitting.get_nb_questions()
            if self.user_answer.order < nb_questions:
                url = reverse(
                    "quiz:sitting_question",
                    args=[self.sitting.id, self.user_answer.order + 1],
                )
                return HttpResponseRedirect(url)
            else:
                # stay on the same question
                print(self.request.POST)
                self.request.POST = {}
                return super().get(self, self.request)

    def validate_answer(self, form):
        self.user_answer.answer = form.cleaned_data["answers"]
        is_correct = self.question.check_if_correct(self.user_answer.answer)

        self.sitting.add_user_progress(self.user_answer.order, is_correct)

        if is_correct is True:
            self.sitting.add_to_score(1)
            self.user_answer.is_correct = True
        else:
            self.user_answer.is_correct = False

        # in study mode, if all questions are answered mark the quiz as completed
        answered, total = self.sitting.progress()
        if self.sitting.mode == SittingMode.STUDY and answered == total:
            self.sitting.mark_quiz_complete()

        self.sitting.save()
        self.user_answer.save()

    def get_success_url(self):
        if self.sitting.mode == SittingMode.STUDY:
            # stay on the same question and show the result
            url = reverse(
                "quiz:sitting_question", args=[self.sitting.id, self.user_answer.order]
            )
        else:
            # redirect to the next question or stay on the last one
            nb_questions = self.sitting.get_nb_questions()
            url = reverse(
                "quiz:sitting_question",
                args=[self.sitting.id, min(self.user_answer.order + 1, nb_questions)],
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
        if self.mode == SittingMode.EXAM and not self.sitting.complete:
            raise Http404
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
        context["score_list"] = self.sitting.get_score_list()
        context["nb_unanswered_questions"] = self.sitting.get_nb_unanswered_questions()
        return context

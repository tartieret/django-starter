from django.urls import path, re_path as url

from app.quiz.views import (
    CategoriesListView,
    QuizDetailView,
    QuizListView,
    # QuizMarkingDetail,
    # QuizMarkingList,
    QuizStart,
    QuizUserProgressView,
    SittingDelete,
    SittingFinish,
    SittingList,
    SittingQuestion,
    SittingQuestionExplanation,
    SittingResults,
    ViewQuizListByCategory,
)

app_name = "quiz"
urlpatterns = [
    url(r"^$", view=QuizListView.as_view(), name="quiz_index"),
    url(
        r"^category/$", view=CategoriesListView.as_view(), name="quiz_category_list_all"
    ),
    url(
        r"^category/(?P<category_name>[\w|\W-]+)/$",
        view=ViewQuizListByCategory.as_view(),
        name="quiz_category_list_matching",
    ),
    url(r"^progress/$", view=QuizUserProgressView.as_view(), name="quiz_progress"),
    # url(r"^marking/$", view=QuizMarkingList.as_view(), name="quiz_marking"),
    # url(
    #     r"^marking/(?P<pk>[\d.]+)/$",
    #     view=QuizMarkingDetail.as_view(),
    #     name="quiz_marking_detail",
    # ),
    url(r"^sitting/$", view=SittingList.as_view(), name="sitting_list"),
    path(
        "sitting/<int:sitting_id>/",
        view=SittingResults.as_view(),
        name="sitting_results",
    ),
    path(
        "sitting/<int:sitting_id>/delete",
        view=SittingDelete.as_view(),
        name="sitting_delete",
    ),
    path(
        "sitting/<int:sitting_id>/finish",
        view=SittingFinish.as_view(),
        name="sitting_finish",
    ),
    path(
        "sitting/<int:sitting_id>/<int:question_order>/",
        view=SittingQuestion.as_view(),
        name="sitting_question",
    ),
    path(
        "sitting/<int:sitting_id>/<int:question_order>/explanation",
        view=SittingQuestionExplanation.as_view(),
        name="sitting_question_explanation",
    ),
    #  passes variable 'quiz_name' to quiz_take view
    url(r"^(?P<slug>[\w-]+)/$", view=QuizDetailView.as_view(), name="quiz_start_page"),
    url(
        r"^(?P<quiz_name>[\w-]+)/take/$", view=QuizStart.as_view(), name="quiz_question"
    ),
]

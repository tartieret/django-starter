from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import (
    Answer,
    Category,
    EssayQuestion,
    Question,
    Quiz,
    MCQuestion,
    OpenQuestion,
    Progress,
    Sitting,
    SubCategory,
    TFQuestion,
    UserAnswer,
)


class AnswerInline(admin.TabularInline):
    model = Answer


class QuizAdminForm(forms.ModelForm):
    """
    below is from
    http://stackoverflow.com/questions/11657682/
    django-admin-interface-using-horizontal-filter-with-
    inline-manytomany-field
    """

    class Meta:
        model = Quiz
        exclude = []

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questions"),
        widget=FilteredSelectMultiple(verbose_name=_("Questions"), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields[
                "questions"
            ].initial = self.instance.question_set.all().select_subclasses()

    def save(self, commit=True):
        quiz = super(QuizAdminForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data["questions"])
        self.save_m2m()
        return quiz


class QuizAdmin(admin.ModelAdmin):
    form = QuizAdminForm

    list_display = (
        "title",
        "category",
    )
    list_filter = ("category",)
    search_fields = (
        "description",
        "category",
    )
    fieldsets = (
        (
            "Publish",
            {
                "fields": (
                    "category",
                    "draft",
                    "url",
                ),
            },
        ),
        (
            "Quiz",
            {
                "fields": (
                    "title",
                    "description",
                    "random_order",
                    "max_questions",
                    "single_attempt",
                    "questions",
                )
            },
        ),
    )


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class MCQuestionAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())

    explanation = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = MCQuestion
        fields = "__all__"


class MCQuestionAdmin(admin.ModelAdmin):
    list_display = ("content",)
    list_filter = ("category",)
    form = MCQuestionAdminForm
    filter_vertical = ("category",)
    fieldsets = (
        (
            None,
            {
                "fields": ("category",),
            },
        ),
        (
            "Add to quiz",
            {
                "classes": ("collapse",),
                "fields": ("quiz",),
            },
        ),
        (
            "Question",
            {
                "fields": (
                    "content",
                    "explanation",
                    "allow_multiple_answers",
                    "answer_order",
                )
            },
        ),
    )

    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)

    inlines = [AnswerInline]


class OpenQuestionAdmin(admin.ModelAdmin):
    list_display = ("content",)
    list_filter = ("category",)
    filter_vertical = ("category",)

    fieldsets = (
        (
            None,
            {
                "fields": ("category",),
            },
        ),
        (
            "Add to quiz",
            {
                "classes": ("collapse",),
                "fields": ("quiz",),
            },
        ),
        (
            "Question",
            {
                "fields": (
                    "content",
                    "explanation",
                )
            },
        ),
        (
            "Answer",
            {
                "fields": (
                    "answer",
                    "answer_type",
                )
            },
        ),
    )


class ProgressAdmin(admin.ModelAdmin):
    """
    to do:
            create a user section
    """

    search_fields = (
        "user",
        "score",
    )


class TFQuestionAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())

    explanation = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = TFQuestion
        fields = "__all__"


class TFQuestionAdmin(admin.ModelAdmin):
    form = TFQuestionAdminForm
    list_display = ("content",)
    list_filter = ("category",)
    filter_vertical = ("category",)
    fieldsets = (
        (
            None,
            {
                "fields": ("category",),
            },
        ),
        (
            "Add to quiz",
            {
                "classes": ("collapse",),
                "fields": ("quiz",),
            },
        ),
        (
            "Question",
            {
                "fields": (
                    "content",
                    "correct",
                    "explanation",
                )
            },
        ),
    )

    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)


class EssayQuestionAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())

    explanation = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = TFQuestion
        fields = "__all__"


class EssayQuestionAdmin(admin.ModelAdmin):
    form = EssayQuestionAdminForm
    list_display = ("content",)
    list_filter = ("category",)
    fields = (
        "content",
        "category",
        "explanation",
        "quiz",
    )
    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer


class SittingAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "quiz",
        "mode",
        "start",
        "end",
        "complete",
        "get_percent_correct",
    )
    inlines = [UserAnswerInline]


admin.site.register(Sitting, SittingAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(MCQuestion, MCQuestionAdmin)
admin.site.register(OpenQuestion, OpenQuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(TFQuestion, TFQuestionAdmin)
admin.site.register(EssayQuestion, EssayQuestionAdmin)

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from ckeditor.widgets import CKEditorWidget

from .models import (
    Answer,
    Category,
    Essay_Question,
    Question,
    Quiz,
    MCQuestion,
    Progress,
    Sitting,
    SubCategory,
    TF_Question,
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


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("category",)


class SubCategoryAdmin(admin.ModelAdmin):
    search_fields = ("sub_category",)
    list_display = (
        "sub_category",
        "category",
    )
    list_filter = ("category",)


class MCQuestionAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())

    explanation = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = MCQuestion
        fields = "__all__"


class MCQuestionAdmin(admin.ModelAdmin):
    list_display = ("content", "category", "sub_category")
    list_filter = ("category",)
    form = MCQuestionAdminForm
    fields = (
        "content",
        "category",
        "sub_category",
        "figure",
        "explanation",
        "quiz",
        "allow_multiple_answers",
        "answer_order",
    )

    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)

    inlines = [AnswerInline]


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
    content = forms.CharField(widget=CKEditorWidget())

    explanation = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = TF_Question
        fields = "__all__"


class TFQuestionAdmin(admin.ModelAdmin):
    form = TFQuestionAdminForm
    list_display = ("content", "category", "sub_category")
    list_filter = ("category",)
    fields = (
        "content",
        "category",
        "sub_category",
        "figure",
        "correct",
        "explanation",
        "quiz",
    )

    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)


class EssayQuestionAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())

    explanation = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = TF_Question
        fields = "__all__"


class EssayQuestionAdmin(admin.ModelAdmin):
    form = EssayQuestionAdminForm
    list_display = ("content", "category", "sub_category")
    list_filter = ("category",)
    fields = (
        "content",
        "category",
        "sub_category",
        "explanation",
        "quiz",
    )
    search_fields = ("content", "explanation")
    filter_horizontal = ("quiz",)


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer


class SittingAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz","mode",  "start", "end", "complete", "get_percent_correct")
    inlines = [UserAnswerInline]


admin.site.register(Sitting, SittingAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(MCQuestion, MCQuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(TF_Question, TFQuestionAdmin)
admin.site.register(Essay_Question, EssayQuestionAdmin)

from django.db import models
from rest_framework import serializers

from app.quiz.models import (
    Answer,
    MCQuestion,
    OpenQuestion,
    Question,
    Quiz,
    TF_Question,
)


# ---------------------------------------------------
# Question serializers
# ---------------------------------------------------


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ("id", "content", "correct")


class MCQuestionSerializer(serializers.ModelSerializer):

    category = serializers.CharField(source="category.category")

    sub_category = serializers.CharField(source="sub_category.sub_category")

    answers = AnswerSerializer(source="answer_set", many=True)

    type = serializers.ReadOnlyField()

    class Meta:
        model = MCQuestion
        fields = "__all__"


class OpenQuestionSerializer(serializers.ModelSerializer):

    category = serializers.CharField(source="category.category")

    sub_category = serializers.CharField(source="sub_category.sub_category")

    type = serializers.ReadOnlyField()

    class Meta:
        model = OpenQuestion
        fields = "__all__"


class TF_QuestionSerializer(serializers.ModelSerializer):

    category = serializers.CharField(source="category.category")

    sub_category = serializers.CharField(source="sub_category.sub_category")

    type = serializers.ReadOnlyField()

    class Meta:
        model = TF_Question
        fields = "__all__"


class QuestionListSerializer(serializers.ListSerializer):

    category = serializers.CharField(source="category.category")

    sub_category = serializers.CharField(source="sub_category.sub_category")

    type = serializers.ReadOnlyField()

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.


        Overwrite default function to select question subclasses
        """
        # Dealing with nested relationships, data can be a Manager,
        # so, first get a queryset from the Manager if needed
        iterable = (
            data.all().select_subclasses() if isinstance(data, models.Manager) else data
        )

        return [self.child.to_representation(item) for item in iterable]


class QuestionSerializer(serializers.ModelSerializer):
    """Generic question serializer"""

    category = serializers.CharField(source="category.category")

    sub_category = serializers.CharField(source="sub_category.sub_category")

    type = serializers.ReadOnlyField()

    class Meta:
        model = Question
        fields = "__all__"
        list_serializer_class = QuestionListSerializer

    def to_representation(self, instance):
        if isinstance(instance, MCQuestion):
            return MCQuestionSerializer(instance=instance).data
        elif isinstance(instance, OpenQuestion):
            return OpenQuestionSerializer(instance=instance).data
        elif isinstance(instance, TF_Question):
            return TF_QuestionSerializer(instance=instance).data
        else:
            return super().to_representation(instance)


# ---------------------------------------------------
# Quiz serializer
# ---------------------------------------------------


class QuizSerializer(serializers.ModelSerializer):

    category = serializers.CharField(source="category.category")

    questions = QuestionSerializer(source="question_set", many=True)

    class Meta:
        model = Quiz
        fields = "__all__"

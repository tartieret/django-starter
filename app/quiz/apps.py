from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QuizConfig(AppConfig):
    name = "app.quiz"
    verbose_name = _("Quiz")

    def ready(self):
        try:
            import app.quiz.signals  # noqa F401
        except ImportError:
            pass

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MainConfig(AppConfig):
    name = "app.main"
    verbose_name = _("Main App")

    def ready(self):
        try:
            import logbook.app.signals  # noqa F401
        except ImportError:
            pass

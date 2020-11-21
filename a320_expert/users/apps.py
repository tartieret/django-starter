from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "a320_expert.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import a320_expert.users.signals  # noqa F401
        except ImportError:
            pass

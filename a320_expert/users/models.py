from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, DateField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


GENDER = [
    ("male", _("Male")),
    ("female", _("Female")),
    ("other", _("Other")),
    ("wontsay", _("Won't say")),
]

LANGUAGES = [("en-us", "English (US)")]



class User(AbstractUser):
    """Default user for A320 Expert."""

    objects = CustomUserManager()

    username = None
    email = EmailField(_("Email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)

    birthdate = DateField(
        verbose_name=_("Birthdate"),
        help_text=_("User birth date"),
        blank=True,
        null=True,
    )

    gender = CharField(
        max_length=10,
        choices=GENDER,
        help_text=_("Gender"),
        verbose_name=_("Gender"),
        default="wontsay",
    )

    language = CharField(
        max_length=8,
        default="en-us",
        choices=LANGUAGES,
        verbose_name=_("Language"),
        help_text=_("User language"),
    )

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", args[self.request.user])

    def __str__(self):
        return self.email

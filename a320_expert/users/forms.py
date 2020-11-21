from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from a320_expert.users.models import GENDER


User = get_user_model()


class UserChangeForm(auth_forms.UserChangeForm):

    error_messages = {"duplicate_email": _("This email has already been taken.")}

    gender = forms.ChoiceField(choices=GENDER, widget=forms.RadioSelect())

    class Meta:
        model = User
        fields = ["name", "email", "gender", "language"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        raise ValidationError(self.error_messages["duplicate_email"])


class UserCreationForm(auth_forms.UserCreationForm):

    error_message = auth_forms.UserCreationForm.error_messages.update(
        {"duplicate_email": _("This email has already been taken.")}
    )

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        raise ValidationError(self.error_messages["duplicate_email"])


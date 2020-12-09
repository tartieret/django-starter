import logging

from django.conf import settings
from django import forms
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field

logger = logging.getLogger(__name__)


class ContactForm(forms.Form):
    """Contact form"""

    name = forms.CharField(max_length=150, label=_("Name"), required=True)
    email = forms.EmailField(required=True, label=_("Email"))
    subject = forms.CharField(
        max_length=150,
        label=_("Subject"),
        required=True,
    )
    message = forms.CharField(widget=forms.Textarea, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "id-contact"
        self.helper.form_class = "contact"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("contact")

        self.helper.layout = Layout(
            Field("name"),
            Field("email"),
            Field("subject"),
            Field("message", rows=4),
            Div(
                Submit(
                    "send",
                    _("Send"),
                    css_class="btn btn-primary btn-wide transition-3d-hover mb-4",
                ),
                css_class="text-center",
            ),
        )

    def send_email(self):
        """Send the contact message to site admins"""
        logger.info("Send contact email")
        name = self.cleaned_data.get("name")
        subject = "[Contact on A320Expert] " + self.cleaned_data.get("subject")
        from_email = self.cleaned_data.get("email")
        message = f"Message from {name}:\n\n" + self.cleaned_data.get("message")
        send_mail(subject, message, from_email, settings.ADMINS)

import logging

from django.contrib import messages
from django.views.generic import FormView
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from app.main.forms import ContactForm

logger = logging.getLogger(__name__)


class ContactView(FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm

    def form_valid(self, form):
        try:
            form.send_email()
            return super().form_valid(form)
        except Exception as error:
            logger.exception(
                "Failed to send contact email: %s", str(error), exc_info=True
            )
            messages.add_message(
                self.request,
                messages.ERROR,
                _("An error occured. Please try again later."),
            )
        return super().form_invalid(form)

    def get_success_url(self):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _("Your message was sent, we will get back to you shortly."),
        )
        return reverse("contact")

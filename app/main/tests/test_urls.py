import pytest
from django.urls import resolve, reverse

from app.users.models import User

pytestmark = pytest.mark.django_db


def test_contact():
    """Url reverse for contact page"""
    assert reverse("contact") == "/contact/"
    assert resolve("/contact/").view_name == "contact"


def test_about():
    """Url reverse for about page"""
    assert reverse("about") == "/about/"
    assert resolve("/about/").view_name == "about"


def test_home():
    """Url reverse for home page"""
    assert reverse("home") == "/"
    assert resolve("/").view_name == "home"

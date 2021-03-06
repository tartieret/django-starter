import re

from django.db import models
from django.utils.translation import gettext_lazy as _


class CategoryManager(models.Manager):
    def new_category(self, name):
        new_category = self.create(name=re.sub(r"\s+", "-", category).lower())

        new_category.save()
        return new_category


class Category(models.Model):

    name = models.CharField(
        verbose_name=_("Name"), max_length=250, blank=True, unique=True, null=True
    )

    description = models.CharField(
        verbose_name=_("Description"), max_length=150, blank=True, default=""
    )

    objects = CategoryManager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class SubCategory(models.Model):

    name = models.CharField(
        verbose_name=_("Name"), max_length=250, blank=True, null=True
    )

    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        verbose_name=_("Category"),
        on_delete=models.CASCADE,
    )

    objects = CategoryManager()

    class Meta:
        verbose_name = _("Sub-Category")
        verbose_name_plural = _("Sub-Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name + " (" + self.category.name + ")"

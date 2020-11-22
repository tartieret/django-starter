import re

from django.db import models
from django.utils.translation import ugettext_lazy as _


class CategoryManager(models.Manager):
    def new_category(self, category):
        new_category = self.create(category=re.sub(r"\s+", "-", category).lower())

        new_category.save()
        return new_category


class Category(models.Model):

    category = models.CharField(
        verbose_name=_("Category"), max_length=250, blank=True, unique=True, null=True
    )

    objects = CategoryManager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["category"]

    def __str__(self):
        return self.category


class SubCategory(models.Model):

    sub_category = models.CharField(
        verbose_name=_("Sub-Category"), max_length=250, blank=True, null=True
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
        ordering = ["sub_category"]

    def __str__(self):
        return self.sub_category + " (" + self.category.category + ")"

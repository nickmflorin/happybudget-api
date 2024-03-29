from django.core.validators import MinLengthValidator
from django.db import models

from happybudget.app.models import BaseModel
from happybudget.app.user.mixins import ModelOwnershipMixin

from .managers import HeaderTemplateManager


def upload_to(instance, filename):
    return instance.user_owner.upload_image_to(
        filename=filename,
        directory="exports/templates"
    )


class HeaderTemplate(
    BaseModel(polymorphic=False, updated_by=None),
    ModelOwnershipMixin
):
    name = models.CharField(
        max_length=32,
        blank=False,
        validators=[MinLengthValidator(1)]
    )
    header = models.TextField(null=True)
    left_info = models.TextField(null=True)
    right_info = models.TextField(null=True)
    left_image = models.ImageField(upload_to=upload_to, null=True)
    right_image = models.ImageField(upload_to=upload_to, null=True)
    user_ownership_field = 'created_by'
    objects = HeaderTemplateManager()

    class Meta:
        verbose_name = "Header Template"
        verbose_name_plural = "Header Templates"
        unique_together = (('created_by', 'name'))

    def __str__(self):
        return "Header Template: %s" % self.name

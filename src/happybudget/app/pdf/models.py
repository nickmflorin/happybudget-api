from django.core.validators import MinLengthValidator
from django.db import models

from happybudget.app.io.utils import upload_user_image_to
from happybudget.app.user.mixins import ModelOwnershipMixin


def upload_to(instance, filename):
    return upload_user_image_to(
        user=instance.user_owner,
        filename=filename,
        directory="exports/templates"
    )


class HeaderTemplate(models.Model, ModelOwnershipMixin):
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        on_delete=models.CASCADE,
        related_name="header_templates"
    )
    ownership_field = 'created_by'

    class Meta:
        verbose_name = "Header Template"
        verbose_name_plural = "Header Templates"
        unique_together = (('created_by', 'name'))

    def __str__(self):
        return "Header Template: %s" % self.name

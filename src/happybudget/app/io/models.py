from django.db import models

from happybudget.app import model
from happybudget.app.models import BaseModel
from happybudget.app.user.mixins import ModelOwnershipMixin

from .managers import AttachmentManager
from .utils import get_extension


def upload_attachment_to(instance, filename):
    return instance.user_owner.upload_file_to(
        filename=filename,
        directory="attachments"
    )


@model.model(type="attachment")
class Attachment(
    BaseModel(polymorphic=False, updated_by=None),
    ModelOwnershipMixin
):
    file = models.FileField(upload_to=upload_attachment_to, null=False)
    user_ownership_field = 'created_by'
    objects = AttachmentManager()

    class Meta:
        get_latest_by = "created_at"
        ordering = ('-created_at', )
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"

    def is_empty(self):
        m2m_related_fields = [
            related.get_accessor_name()
            for related in self._meta.related_objects
        ]
        return all([
            getattr(self, m2m_related_field).count() == 0
            for m2m_related_field in m2m_related_fields
        ])

    def get_extension(self, **kwargs):
        return get_extension(self.file, **kwargs)

from django.db import models

from happybudget.app.models import BaseModel
from happybudget.app.io.utils import upload_user_file_to
from happybudget.app.user.mixins import ModelOwnershipMixin


def upload_attachment_to(instance, filename):
    return upload_user_file_to(
        user=instance.user_owner,
        filename=filename,
        directory="attachments"
    )


class Attachment(
    BaseModel(polymorphic=False, updated_by=None),
    ModelOwnershipMixin
):
    file = models.FileField(upload_to=upload_attachment_to, null=False)
    user_ownership_field = 'created_by'

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

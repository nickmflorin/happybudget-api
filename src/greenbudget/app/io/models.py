from django.db import models

from greenbudget.app.io.utils import upload_user_file_to
from greenbudget.app.user.mixins import ModelOwnershipMixin


def upload_attachment_to(instance, filename):
    return upload_user_file_to(
        user=instance.user_owner,
        filename=filename,
        directory="attachments"
    )


class Attachment(models.Model, ModelOwnershipMixin):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='attachments',
        on_delete=models.CASCADE,
        editable=False
    )
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

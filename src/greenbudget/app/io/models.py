from django.db import models

from greenbudget.app.io.utils import upload_user_file_to


def upload_to(instance, filename):
    return upload_user_file_to(
        user=instance.created_by,
        filename=filename,
        directory="attachments"
    )


class Attachment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='attachments',
        on_delete=models.CASCADE,
        editable=False
    )
    file = models.FileField(upload_to=upload_to, null=False)

    class Meta:
        get_latest_by = "created_at"
        ordering = ('-created_at', )
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"

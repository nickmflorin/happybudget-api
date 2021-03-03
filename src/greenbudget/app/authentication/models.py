import time
import uuid

from django.db import models


def time_random_uuid():
    return str(uuid.uuid1()) + str(int(time.time()))


class ResetUID(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    token = models.CharField(
        max_length=1024,
        unique=True,
        default=time_random_uuid
    )
    used = models.BooleanField(default=False)
    user = models.ForeignKey(
        to='user.User',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "ResetUID"
        verbose_name_plural = "ResetUIDs"

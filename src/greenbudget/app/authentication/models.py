import datetime
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AnonymousShareToken:
    is_authenticated = False


class ShareToken(models.Model):
    is_authenticated = True
    public_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    private_id = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_%(class)ss',
        on_delete=models.CASCADE,
        editable=False
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='Account')
        | models.Q(app_label='subaccount', model='SubAccount')
    )
    expires_at = models.DateTimeField(null=True)
    object_id = models.PositiveIntegerField(db_index=True)
    instance = GenericForeignKey('content_type', 'object_id')

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Share Token"
        verbose_name_plural = "Share Tokens"
        # Note that this unique together constraint effectively makes the GFK
        # a OneToOneField (there is no built in Generic OneToOneField). Right
        # now, we are restricting ShareToken(s) to 1 token per user/instance,
        # but that might change in the future - in which case we can remove this
        # constraint.
        unique_together = (('content_type', 'object_id'))

    def __str__(self):
        return str(self.public_id)

    @property
    def is_expired(self):
        # Note: There is a slight problem with these tokens auto-expiring, and
        # it has to do with the budget detail endpoint being cached.  There is
        # no way to programatically invalidate that cache after the token
        # expires - but that cache invalidates often enough that it should be
        # ok.
        tz = self.created_by.timezone or datetime.timezone.utc
        return self.expires_at is not None \
            and self.expires_at < datetime.datetime.now().replace(tzinfo=tz)

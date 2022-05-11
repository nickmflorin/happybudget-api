from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from happybudget.lib.django_utils.models import Choices
from happybudget.app import model


@model.model(type="collaborator")
class Collaborator(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Even though this is just limited to a Budget right now, eventually, the
    # BudgetAccount and BudgetSubAccount will have a notion of collaboration
    # that is separate from the Budget they are related to.
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='budget', model='Budget')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    instance = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(
        to='user.User',
        related_name='collaborations',
        on_delete=models.CASCADE,
        editable=False
    )

    ACCESS_TYPES = Choices(
        (0, "view_only", "View Only"),
        (1, "editor", "Editor"),
        (2, "owner", "Owner"),
    )
    access_type = models.IntegerField(
        choices=ACCESS_TYPES,
        default=ACCESS_TYPES.view_only,
        null=False
    )

    pre_save_validators = [
        model.PreSaveValidator(
            check=lambda obj:
            obj.user.is_active and obj.user.is_verified,
            message=(
                "A collaborator can only be associated with active, verified "
                "users."
            )
        ),
        model.PreSaveValidator(
            check=lambda obj: hasattr(obj.instance, 'user_owner'),
            message=(
                "Collaborators can only be created for instances that dictate "
                "ownership."
            )
        ),
        model.PreSaveValidator(
            check=lambda obj: obj.instance.user_owner != obj.user,
            message=(
                "A user cannot be assigned as a collaborator for an instance "
                "they created."
            )
        )
    ]

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Collaborator"
        verbose_name_plural = "Collaborators"
        unique_together = (('content_type', 'object_id', 'user'))

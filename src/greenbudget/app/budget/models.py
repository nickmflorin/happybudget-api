from model_utils import Choices
from polymorphic.models import PolymorphicModel

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseBudget(PolymorphicModel):
    author = models.ForeignKey(
        to='user.User',
        related_name='budgets',
        on_delete=models.CASCADE,
    )
    project_number = models.IntegerField(default=0)

    PRODUCTION_TYPES = Choices(
        (0, "film", _("Film")),
    )
    production_type = models.IntegerField(
        choices=PRODUCTION_TYPES,
        default=PRODUCTION_TYPES.film
    )

    created_at = models.DateTimeField(auto_now_add=True)
    shoot_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(default=timezone.now)

    build_days = models.IntegerField(default=0)
    prelight_days = models.IntegerField(default=0)
    studio_shoot_days = models.IntegerField(default=0)
    location_days = models.IntegerField(default=0)

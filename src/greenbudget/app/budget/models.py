from model_utils import Choices
from polymorphic.models import PolymorphicModel

from django.db import models
from django.utils import timezone


class Budget(PolymorphicModel):
    name = models.CharField(max_length=256)
    author = models.ForeignKey(
        to='user.User',
        related_name='budgets',
        on_delete=models.CASCADE,
    )
    project_number = models.IntegerField(default=0)

    PRODUCTION_TYPES = Choices(
        (0, "film", "Film"),
        (1, "episodic", "Episodic"),
        (2, "music", "Music"),
        (3, "commercial", "Commercial"),
        (4, "documentary", "Documentary"),
        (5, "custom", "Custom"),
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

    @property
    def production_type_name(self):
        return self.PRODUCTION_TYPES[self.production_type]

from model_utils import Choices
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from greenbudget.app.account.models import Account
from greenbudget.app.comment.models import Comment

from .exceptions import BudgetPermissionError
from .managers import BudgetManager


class Budget(PolymorphicModel):
    type = "budget"
    name = models.CharField(max_length=256)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='budgets',
        on_delete=models.CASCADE,
    )
    project_number = models.IntegerField(default=0)

    PRODUCTION_TYPES = Choices(
        (0, "film", "Film"),
        (1, "episodic", "Episodic"),
        (2, "music_video", "Music Video"),
        (3, "commercial", "Commercial"),
        (4, "documentary", "Documentary"),
        (5, "custom", "Custom"),
    )
    production_type = models.IntegerField(
        choices=PRODUCTION_TYPES,
        default=PRODUCTION_TYPES.film
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shoot_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(default=timezone.now)

    build_days = models.IntegerField(default=0)
    prelight_days = models.IntegerField(default=0)
    studio_shoot_days = models.IntegerField(default=0)
    location_days = models.IntegerField(default=0)

    trash = models.BooleanField(default=False)

    comments = GenericRelation(Comment)
    objects = BudgetManager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-updated_at', )
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        unique_together = (('created_by', 'name'), )

    def __str__(self):
        return "<{cls} id={id}, name={name}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name
        )

    @property
    def production_type_name(self):
        return self.PRODUCTION_TYPES[self.production_type]

    def to_trash(self):
        self.trash = True
        self.save()

    def restore(self):
        self.trash = False
        self.save()

    def raise_no_access(self, user):
        if user != self.created_by:
            raise BudgetPermissionError()

    @property
    def accounts(self):
        return Account.objects.filter(budget=self)

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return float(self.estimated) - float(self.actual)
        return None

    @property
    def actual(self):
        actuals = []
        for account in self.accounts.all():
            if account.actual is not None:
                actuals.append(account.actual)
        if len(actuals) != 0:
            return sum(actuals)
        return None

    @property
    def estimated(self):
        estimated = []
        for account in self.accounts.all():
            if account.estimated is not None:
                estimated.append(account.estimated)
        if len(estimated) != 0:
            return sum(estimated)
        return None

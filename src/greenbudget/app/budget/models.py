import functools
from model_utils import Choices
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from greenbudget.app import signals
from greenbudget.app.comment.models import Comment
from greenbudget.app.group.models import Group
from greenbudget.app.user.utils import upload_user_image_to

from .duplication import BudgetDuplicator
from .managers import BudgetManager, BaseBudgetManager


def upload_to(instance, filename):
    return upload_user_image_to(
        user=instance.created_by,
        filename=filename,
        directory="budgets"
    )


class BaseBudget(PolymorphicModel):
    name = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='budgets',
        on_delete=models.CASCADE,
        editable=False
    )
    estimated = models.FloatField(default=0.0)
    actual = models.FloatField(default=0.0)
    fringe_contribution = models.FloatField(default=0.0)
    markup_contribution = models.FloatField(default=0.0)
    image = models.ImageField(upload_to=upload_to, null=True)

    groups = GenericRelation(Group)

    objects = BaseBudgetManager()
    non_polymorphic = models.Manager()

    FIELDS_TO_DERIVE = ()
    FIELDS_TO_DUPLICATE = (
        'image', 'name', 'actual', 'estimated', 'fringe_contribution',
        'markup_contribution'
    )

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-updated_at', )
        verbose_name = "Base Budget"
        verbose_name_plural = "Base Budgets"

    def __str__(self):
        return "Budget: %s" % self.name

    def duplicate(self, user):
        duplicator = BudgetDuplicator(self, user)
        return duplicator.duplicate()

    @property
    def fringed_estimated(self):
        return self.estimated + self.fringe_contribution

    @property
    def real_estimated(self):
        return self.fringed_estimated + self.markup_contribution

    def establish_estimated(self, commit=False, accounts=None):
        accounts = accounts or self.children.only('estimated').all()
        self.estimated = functools.reduce(
            lambda current, sub: current + sub.estimated,
            accounts,
            0
        )
        if commit:
            self.save(update_fields=['estimated'])

    def establish_actual(self, commit=False, accounts=None):
        accounts = accounts or self.children.only('actual').all()
        self.actual = functools.reduce(
            lambda current, sub: current + sub.actual,
            accounts,
            0
        )
        if commit:
            self.save(update_fields=['actual'])

    def establish_fringe_contribution(self, commit=False, accounts=None):
        accounts = accounts or self.children.only('fringe_contribution').all()
        self.fringe_contribution = functools.reduce(
            lambda current, sub: current + sub.fringe_contribution,
            accounts,
            0
        )
        if commit:
            self.save(update_fields=['fringe_contribution'])

    def establish_markup_contribution(self, commit=False, accounts=None):
        accounts = accounts or self.children.only('markup_contribution').all()
        self.markup_contribution = functools.reduce(
            lambda current, sub: current + sub.markup_contribution,
            accounts,
            0
        )
        if commit:
            self.save(update_fields=['markup_contribution'])

    def establish_contributions(self, commit=False, accounts=None):
        accounts = accounts or self.children.only(
            'markup_contribution', 'fringe_contribution').all()
        self.establish_fringe_contribution(accounts=accounts)
        # Markups are applied after the Fringes are applied to the value.
        self.establish_markup_contribution(accounts=accounts)
        if commit:
            self.save(
                update_fields=['fringe_contribution', 'markup_contribution'])

    def establish_all(self, commit=False):
        accounts = self.children.only(
            'markup_contribution', 'fringe_contribution', 'estimated').all()
        self.establish_estimated(accounts=accounts)
        self.establish_contributions(accounts=accounts)
        if commit:
            self.save(update_fields=[
                'fringe_contribution', 'markup_contribution', 'estimated'])


@signals.model(flags='suppress_budget_update')
class Budget(BaseBudget):
    type = "budget"

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
    shoot_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(default=timezone.now)
    build_days = models.IntegerField(default=0)
    prelight_days = models.IntegerField(default=0)
    studio_shoot_days = models.IntegerField(default=0)
    location_days = models.IntegerField(default=0)

    comments = GenericRelation(Comment)

    objects = BudgetManager()
    non_polymorphic = models.Manager()

    FIELDS_TO_DUPLICATE = BaseBudget.FIELDS_TO_DUPLICATE + (
        'project_number', 'production_type', 'shoot_date', 'delivery_date',
        'build_days', 'prelight_days', 'studio_shoot_days', 'location_days'
    )

    class Meta(BaseBudget.Meta):
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"

    @property
    def child_instance_cls(self):
        from greenbudget.app.account.models import BudgetAccount
        return BudgetAccount

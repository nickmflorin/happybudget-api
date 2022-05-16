import copy

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from happybudget.lib.utils import cumulative_sum

from happybudget.app import model
from happybudget.app.authentication.models import PublicToken
from happybudget.app.budgeting.decorators import children_method_handler
from happybudget.app.budgeting.models import BudgetingTreePolymorphicModel
from happybudget.app.collaborator.models import Collaborator
from happybudget.app.group.models import Group
from happybudget.app.markup.models import Markup
from happybudget.app.io.utils import upload_user_image_to
from happybudget.app.user.mixins import ModelOwnershipMixin

from .managers import BudgetManager, BaseBudgetManager


def upload_to(instance, filename):
    return upload_user_image_to(
        user=instance.user_owner,
        filename=filename,
        directory="budgets"
    )


ESTIMATED_FIELDS = (
    'accumulated_value',
    'accumulated_markup_contribution',
    'accumulated_fringe_contribution'
)
CALCULATED_FIELDS = ESTIMATED_FIELDS + ('actual', )


class BaseBudget(BudgetingTreePolymorphicModel, ModelOwnershipMixin):
    name = models.CharField(max_length=256)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_budgets',
        on_delete=models.CASCADE,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='budgets',
        on_delete=models.CASCADE,
        editable=False
    )
    # We have to include a long max length in the case that the file name is
    # nested inside many directories and is long.  This happens mostly in tests,
    # but does not hurt to have set outside of tests.
    image = models.ImageField(upload_to=upload_to, null=True, max_length=256)

    ESTIMATED_FIELDS = ESTIMATED_FIELDS
    CALCULATED_FIELDS = CALCULATED_FIELDS

    actual = models.FloatField(default=0.0)
    accumulated_value = models.FloatField(default=0.0)
    accumulated_fringe_contribution = models.FloatField(default=0.0)
    accumulated_markup_contribution = models.FloatField(default=0.0)

    is_deleting = models.BooleanField(default=False)

    groups = GenericRelation(Group)
    children_markups = GenericRelation(Markup)
    public_tokens = GenericRelation(PublicToken)

    objects = BaseBudgetManager()
    non_polymorphic = models.Manager()
    user_ownership_field = 'created_by'

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-updated_at', )
        verbose_name = "Base Budget"
        verbose_name_plural = "Base Budgets"

    def __str__(self):
        return "Budget: %s" % self.name

    @property
    def public_token(self):
        return self.public_tokens.first()

    @property
    def child_instance_cls(self):
        return self.account_cls

    @property
    def nominal_value(self):
        return self.accumulated_value

    @property
    def realized_value(self):
        return self.nominal_value + self.accumulated_fringe_contribution \
            + self.accumulated_markup_contribution

    def mark_updated(self, user=None):
        """
        Marks the :obj:`BaseBudget` instance as having been updated by a
        specific :obj:`User`.  This is only pertinent when the update is
        performed inside of the request context with an actively logged in
        :obj:`User`.
        """
        assert user is None or user.is_fully_authenticated, \
            "A user that is not fully authenticated should not be " \
            "permissioned to update any entities!"
        self.updated_by = user
        self.save(update_fields=['updated_at', 'updated_by'])

    @children_method_handler
    def accumulate_value(self, children):
        previous_value = self.accumulated_value
        self.accumulated_value = cumulative_sum(children, attr='nominal_value')
        return previous_value != self.accumulated_value

    @children_method_handler
    def accumulate_markup_contribution(self, children, to_be_deleted=None):
        markups = self.children_markups.filter(unit=Markup.UNITS.flat).exclude(
            pk__in=to_be_deleted or [],
        )
        previous_value = self.accumulated_markup_contribution
        self.accumulated_markup_contribution = cumulative_sum(
            children,
            attr=['markup_contribution', 'accumulated_markup_contribution'],
        ) + cumulative_sum(markups, attr='rate', ignore_values=None)
        return self.accumulated_markup_contribution != previous_value

    @children_method_handler
    def accumulate_fringe_contribution(self, children):
        previous_value = self.accumulated_fringe_contribution
        self.accumulated_fringe_contribution = cumulative_sum(
            children, attr='accumulated_fringe_contribution')
        return self.accumulated_fringe_contribution != previous_value

    @children_method_handler
    def estimate(self, children, **kwargs):
        alterations = [
            self.accumulate_value(children),
            self.accumulate_fringe_contribution(children),
            self.accumulate_markup_contribution(
                children,
                to_be_deleted=kwargs.get('markups_to_be_deleted', [])
            )
        ]
        if any(alterations) and kwargs.get('commit', False):
            self.save()
        return any(alterations)

    @children_method_handler
    def calculate(self, children, **kwargs):
        return self.estimate(children, **kwargs)

    def save(self, *args, **kwargs):
        if self.id is None and self.updated_by is None \
                and self.created_by is not None:
            self.updated_by = self.created_by
        super().save(*args, **kwargs)


@model.model(type='budget')
class Budget(BaseBudget):
    archived = models.BooleanField(default=False)

    collaborators = GenericRelation(Collaborator)
    objects = BudgetManager()
    non_polymorphic = models.Manager()

    pdf_type = "pdf-budget"
    static_domain = "budget"

    class Meta(BaseBudget.Meta):
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"

    @property
    def is_first_created(self):
        first_created = type(self).objects \
            .filter(created_by=self.created_by) \
            .only('pk') \
            .order_by('created_at').first()
        # Since this property is on an instance that exists, it should be
        # guaranteed that the query returns at least 1 result unless the budget
        # was just deleted.
        assert first_created is not None, \
            "Cannot access property for budgets that were just deleted."
        return first_created.id == self.id

    @children_method_handler
    def actualize(self, children, **kwargs):
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', []) or []

        previous_value = self.actual
        self.actual = cumulative_sum(
            self.children_markups.exclude(pk__in=markups_to_be_deleted),
            attr='actual',
        ) + cumulative_sum(children, attr='actual')
        if previous_value != self.actual and kwargs.get('commit', False):
            self.save(update_fields=['actual'])
        return previous_value != self.actual

    @children_method_handler
    def calculate(self, children, **kwargs):
        commit = kwargs.pop('commit', False)

        alteration_kwargs = copy.deepcopy(kwargs)
        alteration_kwargs.update(commit=False, children=children)
        alterations = [
            super().calculate(**alteration_kwargs),
            self.actualize(**alteration_kwargs)
        ]
        if any(alterations) and commit:
            self.save()
        return any(alterations)

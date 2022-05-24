from django.db import models, IntegrityError

from happybudget.lib.utils import humanize_list, get_attribute

from happybudget.app.models import BaseModel
from happybudget.app.tabling.models import (
    RowModel, OrderedRowModel, OrderedRowPolymorphicModel)

from .utils import AssociatedModel, entity_text


class DomainAccessor:
    """
    Descriptor that returns the Budget domain for the current model, which will
    either be the statically defined domain on the model class or the realized
    domain that takes into consideration the current instance of the model.

    For some budget related models, the model class itself is enough to
    completely determine whether or not the model and instance is associated
    with the "budget" or the "template" domain.

    Example:
    -------
    For example, the :obj:`BudgetAccount` model will only ever be applicable for
    the "budget" domain, which is completely independent from the specific
    instance of :obj:`BudgetAccount` that we are accessing the domain for.

    This means that we can simply define the `static_domain` on the model:

    >>> class BudgetAccount(...):
    >>>     static_domain = "budget"

    And both the model class and instances of the class will always have the
    same domain:

    >>> BudgetAccount.domain
    >>> "budget"
    >>> BudgetAccount.objects.first().domain
    >>> "budget"

    For other budget related models, the model class itself is not enough to
    determine the the specific domain that the model is associated with - this
    is because the model class instances can belong to either of the domain,
    depending on relationships defined on the instance itself.

    Example:
    -------
    For example, the :obj:`Fringe` model can be applicable for either the
    "budget" or the "template" domain, depending on whether or not the `budget`
    field of the :obj:`Fringe` instance is a :obj:`Budget` or a :obj:`Template`.

    This means that the `static_domain` cannot be defined, as we cannot define
    the domain of all instances of the class in the same manner.  This also
    means that a method of determining the `realized_domain` of the :obj:`Fringe`
    must be implemented:

    >>> class Fringe(...):
    >>>     domain_field = 'budget__domain'

    Now, if we try to access the `domain` of the :obj:`Fringe` class statically
    it will return `None`, but instances of the :obj:`Fringe` will appropriately
    return the correct domain the instance belongs to:

    >>> Fringe.domain
    >>> None
    >>> Fringe.objects.first().domain
    >>> "template"
    """
    def __get__(self, obj, objtype=None):
        if obj is not None:
            return obj.realized_domain
        return getattr(objtype, 'static_domain', None)


class BudgetingModelMixin:
    budget_cls = AssociatedModel("budget")
    account_cls = AssociatedModel("account")
    subaccount_cls = AssociatedModel("subaccount")
    domain = DomainAccessor()

    @property
    def realized_domain(self):
        """
        Returns the Budget domain of a model with the properties of the current
        instance taken into consideration.
        """
        if hasattr(self, 'domain_field'):
            domain_field = getattr(self, 'domain_field')
            return get_attribute(domain_field, self, delimiter='__')
        elif self.static_domain is not None:
            return self.static_domain
        raise NotImplementedError(
            f"Domain cannot be determined for an instance of {self.__class__}. "
        )


class BudgetingTreeModelMixin(BudgetingModelMixin):
    @property
    def ancestors(self):
        # If the parent is a Budget or Template, it will not have any ancestors.
        if hasattr(self.parent, 'ancestors'):
            return self.parent.ancestors + [self.parent]
        return [self.parent]

    @property
    def parent_instance_cls(self):
        return type(self.parent)

    @property
    def parent_type(self):
        return self.parent.type

    @property
    def budget(self):
        parent = self.parent
        while hasattr(parent, 'parent'):
            parent = parent.parent
        return parent


class BudgetingModel(models.Model, BudgetingModelMixin):
    class Meta:
        abstract = True


class BudgetingRowModel(RowModel, BudgetingModelMixin):
    class Meta:
        abstract = True


class BudgetingOrderedRowModel(OrderedRowModel, BudgetingModelMixin):
    class Meta:
        abstract = True


class BudgetingTreePolymorphicModel(
    BaseModel(polymorphic=True),
    BudgetingTreeModelMixin
):
    class Meta:
        abstract = True


class BudgetingTreePolymorphicOrderedRowModel(
    OrderedRowPolymorphicModel,
    BudgetingTreeModelMixin
):
    identifier = models.CharField(null=True, max_length=128, blank=True)
    description = models.CharField(null=True, max_length=128, blank=True)
    actual = models.FloatField(default=0.0, blank=True)
    # The nominal values accumulated from all children.
    accumulated_value = models.FloatField(default=0.0)
    # The fringe contributions accumulated from all children.
    accumulated_fringe_contribution = models.FloatField(default=0.0)
    # The contribution of the markups associated with the instance to the
    # instance's estimated value.
    markup_contribution = models.FloatField(default=0.0)
    # The markup contributions accumulated from all children.
    accumulated_markup_contribution = models.FloatField(default=0.0)

    markups = models.ManyToManyField(
        to='markup.Markup',
        related_name='%(class)ss'
    )
    group = models.ForeignKey(
        to='group.Group',
        null=True,
        on_delete=models.SET_NULL,
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return entity_text(self)

    @property
    def VALID_PARENTS(self):
        raise NotImplementedError(
            f"The model {self.__class__} must define a `VALID_PARENTS` "
            "attribute."
        )

    @property
    def valid_parent_cls(self):
        return tuple([getattr(self, attr) for attr in self.VALID_PARENTS])

    def validate_before_save(self):
        super().validate_before_save()
        # If the parent is not specified on the instance, we will get an instance
        # of IntegrityError raised due to the non-nullable field anyways.
        if self.group is not None and self.parent is not None \
                and self.group.parent != self.parent:
            raise IntegrityError(
                "Can only add groups with the same parent as the instance."
            )
        # The `limit_choices_to` property of the content_type ForeignKey field
        # (in the case of a GFK parent) or the the parent ForeignKey field does
        # not actually perform validation before a save, just validation via the
        # Django Admin.  We want to ensure that the parent of the model is
        # valid - even though we will get an error somewhere else if it is not,
        # it is better to perform the validation early here.
        humanized_parents = humanize_list(
            self.valid_parent_cls, conjunction="or")
        # If the parent is None, we will get an IntegrityError when saving
        # regardless, so we do not need to raise one here.
        if self.parent is not None \
                and not isinstance(self.parent, self.valid_parent_cls):
            raise IntegrityError(
                f"Type {type(self.parent)} is not a valid parent for "
                f"{self.__class__.__name__}.  Must be one of "
                f"{humanized_parents}."
            )

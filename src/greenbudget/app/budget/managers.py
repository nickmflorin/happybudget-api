from polymorphic.managers import PolymorphicManager

from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet
from greenbudget.app import signals
from greenbudget.app.budgeting.query import (
    BaseBudgetQuerier as _BaseBudgetQuerier,
    BudgetQuerier as _BudgetQuerier,
)


class BaseBudgetQuerierMixin:
    @signals.disable()
    def bulk_calculate(self, *args, **kwargs):
        return self.bulk_estimate(*args, **kwargs)

    @signals.disable()
    def bulk_estimate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        unsaved_children = kwargs.pop('unsaved_children', {}) or {}
        instances_to_save = set([])
        for obj in instances:
            altered = obj.estimate(
                commit=False,
                unsaved_children=unsaved_children.get(obj.pk),
                **kwargs
            )
            if altered:
                instances_to_save.add(obj)
        if commit:
            self.bulk_update_post_estimation(instances_to_save)
        return instances_to_save


class BaseBudgetQuerier(BaseBudgetQuerierMixin, _BaseBudgetQuerier):
    pass


class BaseBudgetQuery(BaseBudgetQuerier, BulkCreatePolymorphicQuerySet):
    pass


class BaseBudgetManager(BaseBudgetQuerier, PolymorphicManager):
    queryset_class = BaseBudgetQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetQuerier(BaseBudgetQuerierMixin, _BudgetQuerier):
    @signals.disable()
    def bulk_calculate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        instances_to_save = super().bulk_calculate(
            instances=instances,
            commit=False,
            **kwargs
        )
        actualized_instances = self.bulk_actualize(
            instances=instances,
            commit=False,
            **kwargs
        )
        instances_to_save = instances_to_save.union(actualized_instances)
        if commit:
            self.bulk_update_post_calculation(instances_to_save)
        return instances_to_save

    @signals.disable()
    def bulk_actualize(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        unsaved_children = kwargs.pop('unsaved_children', {}) or {}
        instances_to_save = set([])
        for obj in instances:
            altered = obj.actualize(
                commit=False,
                unsaved_children=unsaved_children.get(obj.pk),
                **kwargs
            )
            if altered:
                instances_to_save.add(obj)
        if commit and instances_to_save:
            self.bulk_update_post_actualization(instances_to_save)
        return instances_to_save


class BudgetQuery(BudgetQuerier, BulkCreatePolymorphicQuerySet):
    pass


class BudgetManager(BudgetQuerier, PolymorphicManager):
    queryset_class = BaseBudgetQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

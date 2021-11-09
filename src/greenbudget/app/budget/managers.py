from greenbudget.app import signals
from greenbudget.app.budgeting.managers import BudgetingPolymorphicManager

from .duplication import duplicate


class BaseBudgetManager(BudgetingPolymorphicManager):
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

    def duplicate(self, budget, user, **overrides):
        return duplicate(budget, user, **overrides)


class BudgetManager(BaseBudgetManager):
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

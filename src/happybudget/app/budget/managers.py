from happybudget.lib.utils import ensure_iterable
from happybudget.app import signals
from happybudget.app.budgeting.managers import BudgetingPolymorphicManager
from happybudget.app.budgeting.utils import BudgetTree

from .duplication import Duplicator


class BaseBudgetManager(BudgetingPolymorphicManager):
    @signals.disable()
    def bulk_calculate(self, *args, **kwargs):
        return self.bulk_estimate(*args, **kwargs)

    def perform_bulk_routine(self, instances, method_name, **kwargs):
        instances = ensure_iterable(instances)
        unsaved = kwargs.pop('unsaved_children', {}) or {}

        tree = BudgetTree()

        pass_up_kwargs = dict(**kwargs, **{'commit': False, 'trickle': False})
        for obj in instances:
            altered = getattr(obj, method_name)(
                unsaved_children=unsaved.get(obj.pk),
                **pass_up_kwargs
            )
            if altered:
                tree.add(obj)
        return tree

    @signals.disable()
    def bulk_estimate(self, instances, **kwargs):
        instances = ensure_iterable(instances)
        commit = kwargs.pop('commit', True)
        tree = self.perform_bulk_routine(
            instances=instances,
            method_name='estimate',
            **kwargs
        )
        if commit:
            self.bulk_update_post_est(tree.budgets)
        return tree

    def duplicate(self, budget, user, **overrides):
        duplicator = Duplicator(budget)
        return duplicator(user, **overrides)


class BudgetManager(BaseBudgetManager):
    @signals.disable()
    def bulk_calculate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        tree = super().bulk_calculate(instances, commit=False, **kwargs)
        actualized_tree = self.bulk_actualize(instances, commit=False, **kwargs)
        tree.merge(actualized_tree)
        if commit:
            self.bulk_update_post_calc(tree.budgets)
        return tree

    @signals.disable()
    def bulk_actualize(self, instances, **kwargs):
        instances = ensure_iterable(instances)
        commit = kwargs.pop('commit', True)
        tree = self.perform_bulk_routine(
            instances=instances,
            method_name='actualize',
            **kwargs
        )
        if commit:
            self.bulk_update_post_act(tree.budgets)
        return tree

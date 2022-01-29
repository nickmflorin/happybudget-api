from greenbudget.lib.utils import ensure_iterable

from greenbudget.app import signals
from greenbudget.app.budget.cache import (
    budget_groups_cache,
    budget_instance_cache
)
from greenbudget.app.budgeting.managers import BudgetingPolymorphicRowManager
from greenbudget.app.budgeting.models import BudgetTree

from .cache import account_instance_cache


class AccountManager(BudgetingPolymorphicRowManager):

    @signals.disable()
    def bulk_delete(self, instances):
        budgets = set([inst.budget for inst in instances])
        groups = [obj.group for obj in instances if obj.group is not None]
        # We must invalidate the caches before the delete is performed so
        # we still have access to the PKs.
        account_instance_cache.invalidate(instances)
        budget_groups_cache.invalidate(budgets)

        for obj in instances:
            obj.delete()

        self.mark_budgets_updated(budgets)
        self.bulk_delete_empty_groups(groups)
        self.model.budget_cls.objects.bulk_calculate(budgets)

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        tree = self.bulk_calculate(instances, commit=False)
        account_instance_cache.invalidate(instances)

        groups = []
        if 'group' in update_fields:
            groups = [obj.group for obj in instances if obj.group is not None]

        self.bulk_update(
            instances,
            tuple(self.model.CALCULATED_FIELDS) + tuple(update_fields)
        )
        self.model.budget_cls.objects.bulk_update_post_calc(tree.budgets)
        self.mark_budgets_updated(instances)
        self.bulk_delete_empty_groups(groups)

    @signals.disable()
    def bulk_add(self, instances):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, return_created_objects=True)

        parents = set([inst.parent for inst in created])
        budget_groups_cache.invalidate(parents)
        budget_instance_cache.invalidate(parents)

        self.bulk_calculate(created)
        self.mark_budgets_updated(created)
        return created

    @signals.disable()
    def bulk_calculate(self, *args, **kwargs):
        return self.bulk_estimate(*args, **kwargs)

    def perform_bulk_routine(self, instances, method_name, **kwargs):
        instances = ensure_iterable(instances)
        unsaved = kwargs.pop('unsaved_children', {}) or {}

        tree = BudgetTree()

        pass_up_kwargs = dict(**kwargs, **{'commit': False, 'trickle': False})

        altered_accounts = []
        for obj in instances:
            altered = getattr(obj, method_name)(
                unsaved_children=unsaved.get(obj.pk),
                **pass_up_kwargs
            )
            if altered or obj.was_just_added():
                altered_accounts.append(obj)
                tree.add(obj.parent)

        tree.add(altered_accounts)
        unsaved = self.group_by_parents(altered_accounts)

        for obj in tree.budgets:
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
            self.bulk_update_post_est(tree.accounts)
            self.model.budget_cls.objects.bulk_update_post_est(tree.budgets)
        return tree


class TemplateAccountManager(AccountManager):
    pass


class BudgetAccountManager(AccountManager):
    @signals.disable()
    def bulk_calculate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        tree = super().bulk_calculate(instances, commit=False, **kwargs)
        actualized_tree = self.bulk_actualize(instances, commit=False, **kwargs)
        tree.merge(actualized_tree)
        if commit:
            self.bulk_update_post_calc(tree.accounts)
            self.model.budget_cls.objects.bulk_update_post_calc(tree.budgets)
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
            self.bulk_update_post_act(tree.accounts)
            self.model.budget_cls.objects.bulk_update_post_act(tree.budgets)
        return tree

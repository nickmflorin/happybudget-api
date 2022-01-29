from greenbudget.lib.utils import concat, ensure_iterable

from greenbudget.app import signals
from greenbudget.app.account.cache import account_instance_cache
from greenbudget.app.budget.cache import (
    budget_actuals_owners_cache,
    budget_instance_cache,
    budget_accounts_cache
)
from greenbudget.app.budgeting.cache import invalidate_markups_cache
from greenbudget.app.budgeting.managers import BudgetingManager
from greenbudget.app.budgeting.query import BudgetAncestorQuerier
from greenbudget.app.subaccount.cache import subaccount_instance_cache
from greenbudget.app.tabling.query import RowQuerySet


class MarkupQuerySet(BudgetAncestorQuerier, RowQuerySet):
    pass


class MarkupManager(BudgetAncestorQuerier, BudgetingManager):
    queryset_class = MarkupQuerySet

    def invalidate_related_caches(self, instances, old_parent=None):
        instances = ensure_iterable(instances)

        budgets = set([inst.budget for inst in instances])
        budget_actuals_owners_cache.invalidate([
            b for b in budgets if b.domain == 'budget'])

        budget_instance_cache.invalidate(budgets, ignore_deps=True)
        budget_accounts_cache.invalidate(budgets, ignore_deps=True)

        # Invalidate the Markup caches of the parents that contain information
        # about the Markup.
        parents = set([obj.parent for obj in instances])
        if old_parent:
            parents.add(old_parent)
        invalidate_markups_cache(parents)

        # A given Account or SubAccount references Markup(s) in their responses.
        accounts = set(concat([list(obj.accounts.all()) for obj in instances]))
        account_instance_cache.invalidate(accounts)
        subaccounts = set(concat([
            list(obj.subaccounts.all()) for obj in instances]))
        subaccount_instance_cache.invalidate(subaccounts)

    @signals.disable()
    def recalculate_associated_instances(self, instances, **kwargs):
        instances = ensure_iterable(instances)

        self.invalidate_related_caches(instances)

        # Actualization does not apply to the Template domain.
        parents_to_reactualize = set([
            obj for obj in [obj.parent for obj in instances]
            if obj.domain == 'budget'
        ])
        # Note: We cannot access instance.children.all() because that will
        # perform a DB query at which point the query will result in 0
        # children since the instance is being deleted.
        objects_to_reestimate = set(concat([
            list(obj.accounts.all()) + list(obj.subaccounts.all())
            for obj in instances
        ]) + [
            obj.parent
            # If the Markup is of type PERCENT, the contribution is not
            # applicable to the parent estimated values directly.
            for obj in instances if obj.unit == self.model.UNITS.flat
        ])

        tree = self.bulk_actualize_all(parents_to_reactualize, **kwargs)
        estimated_tree = self.bulk_estimate_all(objects_to_reestimate, **kwargs)
        tree.merge(estimated_tree)
        # The instances in the tree that were reactualized or reestimated will
        # already have their caches invalidated due to the previous method.
        return tree

    @signals.disable()
    def bulk_delete(self, instances, strict=True):
        budgets = set([inst.budget for inst in instances])
        budget_actuals_owners_cache.invalidate([
            b for b in budgets if b.domain == 'budget'])
        self.recalculate_associated_instances(
            instances,
            markups_to_be_deleted=[obj.pk for obj in instances],
        )
        for obj in instances:
            # We have to be concerned with race conditions here.
            try:
                obj.delete()
            except self.model.DoesNotExist as e:
                if strict:
                    raise e

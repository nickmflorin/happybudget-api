from greenbudget.lib.django_utils.models import generic_fk_instance_change

from greenbudget.app import signals
from greenbudget.app.account.cache import (
    account_instance_cache, account_subaccounts_cache)
from greenbudget.app.budget.cache import budget_instance_cache
from greenbudget.app.budgeting.managers import BudgetingRowManager
from greenbudget.app.subaccount.cache import (
    subaccount_instance_cache, subaccount_subaccounts_cache)


class ActualManager(BudgetingRowManager):
    @signals.disable()
    def bulk_delete(self, instances):
        budgets = set([obj.budget for obj in instances])
        owners = set([obj.owner for obj in instances])

        for obj in instances:
            obj.delete()

        self.mark_budgets_updated(budgets)
        self.bulk_actualize_all(owners)

    @signals.disable()
    def bulk_add(self, instances):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, predetermine_pks=True)

        owners_to_reactualize = set(
            [obj.owner for obj in created if obj.owner is not None])

        self.mark_budgets_updated(created)
        self.bulk_actualize_all(owners_to_reactualize)
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        # Bulk updating can only be done with "concrete fields".  The "owner"
        # field is a GFK.
        if 'owner' in update_fields:
            update_fields = [f for f in update_fields if f != 'owner']
            update_fields = tuple(update_fields) + ('content_type', 'object_id')

        self.bulk_update(instances, update_fields)

        owners_to_reactualize = set([])
        for obj in instances:
            owners_to_reactualize.update(self.get_owners_to_reactualize(obj))

        self.mark_budgets_updated(instances)
        self.bulk_actualize_all(owners_to_reactualize)

    def get_owners_to_reactualize(self, obj):
        owners_to_reactualize = set([])
        # If the Actual is in the midst of being created, we always want
        # to actualize the owners.
        if obj._state.adding is True or obj.was_just_added():
            if obj.owner is not None:
                owners_to_reactualize.add(obj.owner)
        else:
            # We only need to reactualize the owner if the owner was changed
            # or the actual value was changed.
            old_owner, new_owner = generic_fk_instance_change(obj)
            if old_owner != new_owner:
                owners_to_reactualize.update([
                    x for x in [new_owner, old_owner]
                    if x is not None
                ])
            elif obj.field_has_changed('value') and obj.owner is not None:
                owners_to_reactualize.add(obj.owner)
        return owners_to_reactualize

    def bulk_actualize_all(self, instances, **kwargs):
        tree = super().bulk_actualize_all(instances, **kwargs)
        budget_instance_cache.invalidate(tree.budgets)

        account_instance_cache.invalidate(tree.accounts, ignore_deps=True)
        account_subaccounts_cache.invalidate(tree.accounts)

        subaccount_instance_cache.invalidate(tree.subaccounts, ignore_deps=True)
        subaccount_subaccounts_cache.invalidate(tree.subaccounts)
        return tree

from greenbudget.lib.django_utils.models import generic_fk_instance_change
from greenbudget.lib.utils import split_kwargs

from greenbudget.app import signals
from greenbudget.app.account.cache import account_instance_cache
from greenbudget.app.budget.cache import (
    budget_instance_cache, budget_actuals_cache, budget_children_cache)
from greenbudget.app.budgeting.managers import BudgetingOrderedRowManager
from greenbudget.app.integrations.plaid import client
from greenbudget.app.subaccount.cache import (
    subaccount_instance_cache, invalidate_parent_children_cache)


class ActualManager(BudgetingOrderedRowManager):
    @signals.disable()
    def bulk_delete(self, instances):
        budgets = set([obj.budget for obj in instances])
        budget_actuals_cache.invalidate(budgets)
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

        budgets = set([obj.budget for obj in created])
        budget_actuals_cache.invalidate(budgets)
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        budgets = set([obj.budget for obj in instances])
        budget_actuals_cache.invalidate(budgets)

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

    def bulk_import(self, source, *args, **kwargs):
        imports = {
            self.model.IMPORT_SOURCES.bank_account:
                'import_bank_account_transactions'
        }
        if source not in imports:
            raise ValueError(f"Invalid source {source} provided.")
        return getattr(self, imports[source])(*args, **kwargs)

    def import_bank_account_transactions(self, **kwargs):
        split, model = split_kwargs(
            'raise_exception', 'account_ids', 'start_date', 'end_date',
            'public_token', **kwargs)
        transactions = client.fetch_transactions(model['created_by'], **split)
        return self.bulk_add([
            self.model.from_plaid_transaction(t, **model)
            for t in transactions
        ])

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
        parents = [a.parent for a in tree.accounts]
        budget_children_cache.invalidate(parents)

        subaccount_instance_cache.invalidate(tree.subaccounts, ignore_deps=True)
        parents = [a.parent for a in tree.subaccounts]
        invalidate_parent_children_cache(parents, ignore_deps=True)

        return tree

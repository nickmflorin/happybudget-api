from happybudget.lib.utils import split_kwargs

from happybudget.app import signals
from happybudget.app.account.cache import account_instance_cache
from happybudget.app.budget.cache import (
    budget_instance_cache, budget_actuals_cache, budget_children_cache)
from happybudget.app.budgeting.managers import BudgetingOrderedRowManager
from happybudget.app.subaccount.cache import (
    subaccount_instance_cache, invalidate_parent_children_cache)

from .query import ActualQuerier, ActualQuerySet


class ActualManager(ActualQuerier, BudgetingOrderedRowManager):
    queryset_class = ActualQuerySet

    @signals.disable()
    def bulk_delete(self, instances, request=None):
        budgets = set([obj.budget for obj in instances])
        budget_actuals_cache.invalidate(budgets)

        for obj in instances:
            obj.delete()

        self.reactualize_owners(instances, self.model.actions.DELETE)

        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(budgets, request.user)

    @signals.disable()
    def bulk_add(self, instances, request=None):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, predetermine_pks=True)

        self.reactualize_owners(created, self.model.actions.CREATE)

        budgets = set([obj.budget for obj in created])
        budget_actuals_cache.invalidate(budgets)

        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(created, request.user)
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields, request=None):
        budgets = set([obj.budget for obj in instances])
        budget_actuals_cache.invalidate(budgets)

        # Bulk updating can only be done with "concrete fields".  The "owner"
        # field is a GFK.
        if 'owner' in update_fields:
            update_fields = [f for f in update_fields if f != 'owner']
            update_fields = tuple(update_fields) + ('content_type', 'object_id')

        self.bulk_update(instances, update_fields)
        self.reactualize_owners(instances, self.model.actions.UPDATE)

        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(instances, request.user)

    def bulk_import(self, source, *args, **kwargs):
        imports = {
            self.model.IMPORT_SOURCES.bank_account:
                'import_bank_account_transactions'
        }
        if source not in imports:
            raise ValueError(f"Invalid source {source} provided.")
        return getattr(self, imports[source])(*args, **kwargs)

    def import_bank_account_transactions(self, **kwargs):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.integrations.plaid.api import client
        split, model = split_kwargs(
            'raise_exception', 'account_ids', 'start_date', 'end_date',
            'public_token', **kwargs)
        transactions = client.fetch_transactions(model['created_by'], **split)
        return self.bulk_add([
            self.model.from_plaid_transaction(t, **model)
            for t in transactions if t.should_ignore is False
        ])

    def get_owners_to_reactualize(self, instances, action):
        owners_to_reactualize = set([])
        for obj in instances:
            owners_to_reactualize.update(obj.get_owners_to_reactualize(action))
        return owners_to_reactualize

    def reactualize_owners(self, instances, action, **kwargs):
        owners = self.get_owners_to_reactualize(instances, action)
        return self.bulk_actualize_all(owners, **kwargs)

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

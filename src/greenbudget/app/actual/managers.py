from greenbudget.lib.django_utils.models import generic_fk_instance_change

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_actuals_cache
from greenbudget.app.budgeting.managers import BudgetingManager


class ActualManager(BudgetingManager):
    @signals.disable()
    def bulk_delete(self, instances):
        owners = [obj.owner for obj in instances]
        budgets = set([obj.budget for obj in instances])

        for obj in instances:
            obj.delete()

        self.bulk_actualize_all(set(owners))

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was reactualized.
        for budget in budgets:
            budget_actuals_cache.invalidate(budget)
            budget.mark_updated()

    @signals.disable()
    def bulk_add(self, instances):
        self.validate_instances_before_save(instances)

        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, predetermine_pks=True)

        owners_to_reactualize = set(
            [obj.owner for obj in created if obj.owner is not None])
        self.bulk_actualize_all(owners_to_reactualize)

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was reactualized.
        for budget in set([inst.budget for inst in created]):
            budget_actuals_cache.invalidate(budget)
            budget.mark_updated()

        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        self.validate_instances_before_save(instances)

        # Bulk updating can only be done with "concrete fields".  The "owner"
        # field is a GFK.
        if 'owner' in update_fields:
            update_fields = [f for f in update_fields if f != 'owner']
            update_fields = tuple(update_fields) + ('content_type', 'object_id')

        self.bulk_update(instances, update_fields)

        owners_to_reactualize = set([])
        for obj in instances:
            owners_to_reactualize.update(self.get_owners_to_reactualize(obj))

        self.bulk_actualize_all(owners_to_reactualize)

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was reactualized.
        for budget in set([inst.budget for inst in instances]):
            budget_actuals_cache.invalidate(budget)
            budget.mark_updated()

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
            elif obj.field_has_changed('value'):
                if obj.owner is not None:
                    owners_to_reactualize.add(obj.owner)
        return owners_to_reactualize

    @signals.disable()
    def reactualize_owner(self, obj, deleting=False):
        owners_to_reactualize = self.get_owners_to_reactualize(obj)
        if deleting:
            owners_to_reactualize = set([obj.owner])

        self.bulk_actualize_all(owners_to_reactualize)
        budget_actuals_cache.invalidate(obj.budget)

from greenbudget.lib.utils import concat

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_actuals_owners_cache
from greenbudget.app.budgeting.managers import BudgetingManager
from greenbudget.app.budgeting.query import BudgetAncestorQuerier
from greenbudget.app.tabling.query import RowQuerySet


class MarkupQuerySet(BudgetAncestorQuerier, RowQuerySet):
    pass


class MarkupManager(BudgetAncestorQuerier, BudgetingManager):
    queryset_class = MarkupQuerySet

    @signals.disable()
    def pre_delete(self, instances):
        parents = set([
            obj.intermittent_parent
            for obj in instances if obj.intermittent_parent is not None
        ])
        # Actualization does not apply to the Template domain.
        parents_to_reactualize = set([
            obj for obj in parents
            if obj.domain == 'budget'
        ])
        # Note: We cannot access instance.children.all() because that will
        # perform a DB query at which point the query will result in 0
        # children since the instance is being deleted.
        objects_to_reestimate = set(concat([
            list(obj.accounts.all()) + list(obj.subaccounts.all())
            for obj in instances
        ]) + [
            obj.intermittent_parent
            # If the Markup is of type PERCENT, the contribution is not
            # applicable to the parent estimated values directly.
            for obj in instances if obj.intermittent_parent is not None
            and obj.unit == self.model.UNITS.flat
        ])
        parents = [
            obj.intermittent_parent
            # If the Markup is of type PERCENT, the contribution is not
            # applicable to the parent estimated values directly.
            for obj in instances if obj.intermittent_parent is not None
        ]
        [instance.invalidate_markups_cache() for instance in parents]

        self.bulk_actualize_all(
            instances=parents_to_reactualize,
            markups_to_be_deleted=[obj.pk for obj in instances]
        )
        self.bulk_estimate_all(
            instances=objects_to_reestimate,
            markups_to_be_deleted=[obj.pk for obj in instances]
        )

    def cleanup(self, instances, **kwargs):
        super().cleanup(instances)
        budgets = set([inst.intermittent_budget for inst in instances])
        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was recalculated.
        for budget in [b for b in budgets if b is not None]:
            budget.mark_updated()
            budget_actuals_owners_cache.invalidate(budget)

    @signals.disable()
    def bulk_delete(self, instances, strict=True):
        self.pre_delete(instances)
        for obj in instances:
            # We have to be concerned with race conditions here.
            try:
                obj.delete()
            except self.model.DoesNotExist as e:
                if strict:
                    raise e
        self.cleanup(instances)

    @signals.disable()
    def reestimate_parent(self, obj):
        parents_to_reestimate = obj.get_parents_to_reestimate()
        self.bulk_estimate_all(parents_to_reestimate)

    @signals.disable()
    def reestimate_children(self, obj):
        children_to_reestimate = obj.get_children_to_reestimate()
        self.bulk_estimate_all(children_to_reestimate)

    @signals.disable()
    def reestimate_associated(self, obj):
        to_reestimate = obj.get_parents_to_reestimate()
        to_reestimate.update(obj.get_children_to_reestimate())
        self.bulk_estimate_all(to_reestimate)

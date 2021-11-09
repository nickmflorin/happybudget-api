from greenbudget.lib.django_utils.models import generic_fk_instance_change
from greenbudget.lib.utils import concat

from greenbudget.app import signals
from greenbudget.app.budgeting.managers import BudgetingManager
from greenbudget.app.budgeting.query import (
    BudgetingQuerySet, BudgetAncestorQuerier)


class MarkupQuerier(BudgetAncestorQuerier):
    pass


class MarkupQuery(MarkupQuerier, BudgetingQuerySet):
    pass


class MarkupManager(MarkupQuerier, BudgetingManager):
    queryset_class = MarkupQuery

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
            markups_to_be_deleted=[obj.pk for obj in instances],
            invalidate_caches=False
        )
        self.bulk_estimate_all(
            instances=objects_to_reestimate,
            markups_to_be_deleted=[obj.pk for obj in instances],
            invalidate_caches=False
        )

    @signals.disable()
    def bulk_delete(self, instances, strict=True):
        budgets = set([inst.budget for inst in instances])
        self.pre_delete(instances)
        for obj in instances:
            # We have to be concerned with race conditions here.
            try:
                obj.delete()
            except self.model.DoesNotExist as e:
                if strict:
                    raise e
        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was recalculated.
        for budget in budgets:
            budget.mark_updated()

    def get_parents_to_reestimate(self, obj):
        parents_to_reestimate = set([])
        # If the Markup is in the midst of being created, we always want
        # to estimate the parent.
        if obj._state.adding is True or obj.was_just_added():
            if obj.parent is not None:
                parents_to_reestimate.add(obj.parent)
        else:
            # We only need to reestimate the parent if the parent was changed
            # or the markup unit or rate was changed.
            old_parent, new_parent = generic_fk_instance_change(obj)
            if old_parent != new_parent:
                parents_to_reestimate.update([
                    x for x in [old_parent, new_parent]
                    if x is not None
                ])
            elif obj.fields_have_changed('unit', 'rate') \
                    and obj.parent is not None:
                parents_to_reestimate.add(obj.parent)
        return parents_to_reestimate

    def get_children_to_reestimate(self, obj):
        # If the Markup is in the midst of being created, we always want
        # to estimate the children.
        if obj._state.adding is True or obj.was_just_added() \
                or obj.fields_have_changed('unit', 'rate'):
            return set(
                list(obj.accounts.all()) + list(obj.subaccounts.all()))
        return set()

    @signals.disable()
    def reestimate_parent(self, obj):
        parents_to_reestimate = self.get_parents_to_reestimate(obj)
        self.bulk_estimate_all(parents_to_reestimate)
        obj.budget.mark_updated()

    @signals.disable()
    def reestimate_children(self, obj):
        children_to_reestimate = self.get_children_to_reestimate(obj)
        self.bulk_estimate_all(children_to_reestimate)
        obj.budget.mark_updated()

    @signals.disable()
    def reestimate_associated(self, obj):
        to_reestimate = self.get_parents_to_reestimate(obj)
        to_reestimate.update(self.get_children_to_reestimate(obj))
        self.bulk_estimate_all(to_reestimate)
        obj.budget.mark_updated()

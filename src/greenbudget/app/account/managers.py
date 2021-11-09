from greenbudget.lib.utils import set_or_list

from greenbudget.app import signals
from greenbudget.app.budgeting.managers import BudgetingPolymorphicManager


class AccountManager(BudgetingPolymorphicManager):
    @signals.disable()
    def bulk_delete(self, instances):
        budgets = set([obj.parent for obj in instances])
        groups = [obj.group for obj in instances if obj.group is not None]

        for obj in instances:
            obj.invalidate_caches(trickle=True)
            obj.delete()

        self.bulk_delete_empty_groups(groups)
        self.model.budget_cls().objects.bulk_calculate(budgets)

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was recalculated.
        for budget in set([inst.budget for inst in instances]):
            budget.mark_updated()

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        self.validate_instances_before_save(instances)

        calculated, budgets = self.bulk_calculate(instances, commit=False)
        instances = calculated.union(instances)

        groups = []
        if 'group' in update_fields:
            groups = [obj.group for obj in instances if obj.group is not None]

        # Note: This will more than likely lead to invalidating caches multiple
        # times due to the children invalidating parent caches.  We need to
        # investigate batch catch invalidation with Django/AWS.
        for obj in set_or_list(instances) + set_or_list(budgets):
            obj.invalidate_caches(trickle=True)

        self.bulk_update(
            instances,
            tuple(self.model.CALCULATED_FIELDS) + tuple(update_fields)
        )
        self.model.budget_cls().objects.bulk_update_post_calculation(budgets)

        self.bulk_delete_empty_groups(groups)

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was recalculated.
        for budget in set([inst.budget for inst in instances]):
            budget.mark_updated()

    @signals.disable()
    def bulk_add(self, instances):
        self.validate_instances_before_save(instances)

        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, return_created_objects=True)

        self.bulk_calculate(created)

        # Note: This will more than likely lead to invalidating caches multiple
        # times due to the children invalidating parent caches.  We need to
        # investigate batch catch invalidation with Django/AWS.
        for obj in created:
            obj.invalidate_caches(trickle=True)

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was recalculated.
        for budget in set([inst.budget for inst in instances]):
            budget.mark_updated()
        return created

    @signals.disable()
    def bulk_calculate(self, *args, **kwargs):
        return self.bulk_estimate(*args, **kwargs)

    @signals.disable()
    def bulk_estimate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        unsaved_children = kwargs.pop('unsaved_children', {}) or {}
        instances_to_save = set([])

        budgets_to_reestimate = {}
        for obj in instances:
            assert isinstance(obj, self.model)
            altered = obj.estimate(
                commit=False,
                trickle=False,
                unsaved_children=unsaved_children.get(obj.pk),
                **kwargs
            )
            if altered:
                instances_to_save.add(obj)
            if (altered or obj.was_just_added()) and obj.parent is not None:
                if obj.parent is not None:
                    assert isinstance(obj.parent, self.model.budget_cls())
                    if obj.parent.pk in budgets_to_reestimate:
                        budgets_to_reestimate[obj.parent.pk]['unsaved'].add(obj)
                    else:
                        budgets_to_reestimate[obj.parent.pk] = {
                            'instance': obj.parent,
                            'unsaved': set([obj])
                        }

        budgets_to_save = set([])
        for k, v in budgets_to_reestimate.items():
            obj = v['instance']
            altered = obj.estimate(
                commit=False,
                unsaved_children=v['unsaved'],
                **kwargs
            )
            if altered:
                budgets_to_save.add(obj)

        if commit:
            self.bulk_update_post_estimation(instances_to_save)
            self.model.budget_cls().objects.bulk_update_post_estimation(
                budgets_to_save)

        return instances_to_save, budgets_to_save


class TemplateAccountManager(AccountManager):
    pass


class BudgetAccountManager(AccountManager):
    @signals.disable()
    def bulk_calculate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        instances_to_save, budgets_to_save = super().bulk_calculate(
            instances=instances,
            commit=False,
            **kwargs
        )
        actualized_instances, actualized_budgets = self.bulk_actualize(
            instances=instances,
            commit=False,
            **kwargs
        )
        instances_to_save = instances_to_save.union(actualized_instances)
        budgets_to_save = budgets_to_save.union(actualized_budgets)

        if commit:
            self.bulk_update_post_calculation(instances_to_save)
            self.model.budget_cls().objects.bulk_update_post_calculation(
                budgets_to_save)
        return instances_to_save, budgets_to_save

    @signals.disable()
    def bulk_actualize(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        unsaved_children = kwargs.pop('unsaved_children', {}) or {}
        instances_to_save = set([])

        budgets_to_reactualize = {}
        for obj in instances:
            assert isinstance(obj, self.model)
            altered = obj.actualize(
                commit=False,
                trickle=False,
                unsaved_children=unsaved_children.get(obj.pk),
                **kwargs
            )
            if altered:
                instances_to_save.add(obj)
            if (altered or obj.was_just_added()) and obj.parent is not None:
                if obj.parent is not None:
                    assert isinstance(obj.parent, self.model.budget_cls())
                    if obj.parent.pk in budgets_to_reactualize:
                        budgets_to_reactualize[obj.parent.pk] = {
                            'instance': obj.parent,
                            'unsaved': budgets_to_reactualize[
                                obj.parent.pk]['unsaved'].add(obj)
                        }
                    else:
                        budgets_to_reactualize[obj.parent.pk] = {
                            'instance': obj.parent,
                            'unsaved': set([obj])
                        }

        budgets = set([])
        for k, v in budgets_to_reactualize.items():
            obj = v['instance']
            altered = obj.actualize(
                commit=False,
                unsaved_children=v['unsaved'],
                **kwargs
            )
            if altered:
                budgets.add(obj)

        if commit:
            self.bulk_update_post_actualization(instances_to_save)
            self.model.budget_cls().objects.bulk_update_post_actualization(
                budgets)

        return instances_to_save, budgets

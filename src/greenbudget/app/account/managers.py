from greenbudget.app import signals
from greenbudget.app.budgeting.managers import BudgetingPolymorphicRowManager


class AccountManager(BudgetingPolymorphicRowManager):

    def cleanup(self, instances, mark_budgets=True):
        super().cleanup(instances)
        budgets = set([inst.budget for inst in instances])
        if mark_budgets:
            self.mark_budgets_updated(budgets)

    @signals.disable()
    def bulk_delete(self, instances):
        budgets = set([obj.parent for obj in instances])
        groups = [obj.group for obj in instances if obj.group is not None]

        for obj in instances:
            obj.delete()

        self.cleanup(instances)

        self.bulk_delete_empty_groups(groups)
        self.model.budget_cls.objects.bulk_calculate(budgets)

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        calculated, budgets = self.bulk_calculate(instances, commit=False)
        instances = calculated.union(instances)

        groups = []
        if 'group' in update_fields:
            groups = [obj.group for obj in instances if obj.group is not None]

        self.bulk_update(
            instances,
            tuple(self.model.CALCULATED_FIELDS) + tuple(update_fields),
            mark_budgets=False
        )
        self.model.budget_cls.objects.bulk_update_post_calculation(
            instances=budgets,
            mark_budgets=False
        )

        self.bulk_delete_empty_groups(groups)
        self.mark_budgets_updated(instances)

    @signals.disable()
    def bulk_add(self, instances):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, return_created_objects=True)

        self.bulk_calculate(created)
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
                # We need to include the unsaved children in the estimation
                # method so the method accounts for them in the estimation of
                # the parent.
                unsaved_children=unsaved_children.get(obj.pk),
                **kwargs
            )
            if altered:
                instances_to_save.add(obj)
            # If the Account was altered during the estimation or the Account
            # was just added, the Account's parent (a Budget or Template) must
            # also be reestimated.  Note that `obj.parent is None` is an edge
            # case that can happen during CASCADE deletes.
            if (altered or obj.was_just_added()) and obj.parent is not None:
                assert isinstance(obj.parent, self.model.budget_cls)
                budgets_to_reestimate.setdefault(obj.parent.pk, {
                    'instance': obj.parent,
                    'unsaved': set()
                })
                budgets_to_reestimate[obj.parent.pk]['unsaved'].add(obj)

        budgets_to_save = set([])
        for k, v in budgets_to_reestimate.items():
            obj = v['instance']
            altered = obj.estimate(
                commit=False,
                # We need to include the unsaved children in the estimation
                # method so the method accounts for them in the estimation of
                # the parent.
                unsaved_children=v['unsaved'],
                **kwargs
            )
            if altered:
                budgets_to_save.add(obj)

        if commit:
            self.bulk_update_post_estimation(instances_to_save)
            self.model.budget_cls.objects.bulk_update_post_estimation(
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
            self.model.budget_cls.objects.bulk_update_post_calculation(
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
                # We need to include the unsaved children in the actualization
                # method so the method accounts for them in the actualization of
                # the parent.
                unsaved_children=unsaved_children.get(obj.pk),
                **kwargs
            )
            if altered:
                instances_to_save.add(obj)
            # If the Account was altered during the actualization or the Account
            # was just added, the Account's parent (a Budget or Template) must
            # also be reactualized.  Note that `obj.parent is None` is an edge
            # case that can happen during CASCADE deletes.
            if (altered or obj.was_just_added()) and obj.parent is not None:
                assert isinstance(obj.parent, self.model.budget_cls)
                budgets_to_reactualize.setdefault(obj.parent.pk, {
                    'instance': obj.parent,
                    'unsaved': set()
                })
                budgets_to_reactualize[obj.parent.pk]['unsaved'].add(obj)

        budgets = set([])
        for k, v in budgets_to_reactualize.items():
            obj = v['instance']
            altered = obj.actualize(
                commit=False,
                # We need to include the unsaved children in the actualization
                # method so the method accounts for them in the actualization of
                # the parent.
                unsaved_children=v['unsaved'],
                **kwargs
            )
            if altered:
                budgets.add(obj)

        if commit:
            self.bulk_update_post_actualization(instances_to_save)
            self.model.budget_cls.objects.bulk_update_post_actualization(
                budgets)

        return instances_to_save, budgets

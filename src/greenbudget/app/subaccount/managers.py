from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, Q, When, Value as V, BooleanField

from greenbudget.lib.utils import concat, set_or_list

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_actuals_owner_tree_cache
from greenbudget.app.budgeting.managers import BudgetingPolymorphicRowManager
from greenbudget.app.tabling.query import RowQuerier, RowPolymorphicQuerySet


class SubAccountQuerier(RowQuerier):

    def filter_by_parent(self, parent):
        return self.filter(
            content_type_id=ContentType.objects.get_for_model(type(parent)).id,
            object_id=parent.pk
        )

    def filter_by_budget(self, budget):
        """
        Since the :obj:`subaccount.models.SubAccount` is tied to the a
        :obj:`budget.models.Budget` instance only via an eventual parent
        :obj:`account.models.Account` instance, and the relationship between
        :obj:`subaccount.models.SubAccount` and :obj:`account.models.Account`
        is generic, we have to provide a custom method for filtering the
        :obj:`subaccount.models.SubAccount`(s) by a budget.

        It is important to note that this method is slow, so it should only
        be used sparingly.
        """
        return self.annotate(
            _ongoing=Case(
                When(self._get_case_query(budget), then=V(True)),
                default=V(False),
                output_field=BooleanField()
            )
        ).filter(_ongoing=True)

    def _get_subaccount_levels(self, budget):
        subaccount_levels = []
        subaccounts = concat([
            [q[0] for q in account.children.only('pk').values_list('pk')]
            for account in budget.account_cls().objects.filter(parent=budget)
        ])
        while len(subaccounts) != 0:
            subaccount_levels.append(subaccounts)
            subaccounts = concat([
                [q[0] for q in account.children.only('pk').values_list('pk')]
                for account in self.model.objects
                .prefetch_related('children').filter(id__in=subaccounts)
            ])
        return subaccount_levels

    def _get_case_query(self, budget):
        account_ct = ContentType.objects.get_for_model(budget.account_cls())
        subaccount_ct = ContentType.objects.get_for_model(
            budget.subaccount_cls())
        accounts = [
            q[0] for q in budget.account_cls().objects.filter(parent=budget)
            .only('pk').values_list('pk')
        ]
        query = Q(content_type_id=account_ct) & Q(object_id__in=accounts)
        subaccount_levels = self._get_subaccount_levels(budget)
        for level in subaccount_levels:
            query = query | (
                Q(content_type_id=subaccount_ct) & Q(object_id__in=level))
        return query


class SubAccountQuerySet(SubAccountQuerier, RowPolymorphicQuerySet):
    pass


class SubAccountManager(SubAccountQuerier, BudgetingPolymorphicRowManager):
    queryset_class = SubAccountQuerySet

    def cleanup(self, instances, mark_budgets=True):
        super().cleanup(instances)
        budgets = set([inst.budget for inst in instances])
        if mark_budgets:
            self.mark_budgets(budgets=budgets)
        budget_actuals_owner_tree_cache.invalidate(budgets)

    @signals.disable()
    def bulk_delete(self, instances):
        groups = [obj.group for obj in instances if obj.group is not None]

        for obj in instances:
            obj.delete()

        self.cleanup(instances)

        self.bulk_calculate_all([obj.parent for obj in instances])
        self.bulk_delete_empty_groups(groups)

    @signals.disable()
    def bulk_add(self, instances):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, return_created_objects=True)

        self.bulk_calculate(created)
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        calculated, accounts, budgets = self.bulk_calculate(
            instances, commit=False)
        instances = calculated.union(instances)
        groups = [obj.group for obj in instances if obj.group is not None]

        for obj in set_or_list(instances):
            if obj.children.count() != 0:
                obj.clear_deriving_fields(commit=False)

        self.bulk_update(
            instances,
            tuple(self.model.CALCULATED_FIELDS) + tuple(update_fields),
            mark_budgets=False
        )
        self.model.account_cls().objects.bulk_update_post_calculation(
            accounts,
            mark_budgets=False
        )
        self.model.budget_cls().objects.bulk_update_post_calculation(
            budgets
        )

        self.bulk_delete_empty_groups(groups)
        self.mark_budgets(instances=instances)

    @signals.disable()
    def bulk_calculate(self, *args, **kwargs):
        return self.bulk_estimate(*args, **kwargs)

    @signals.disable()
    def bulk_estimate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        unsaved_children = kwargs.pop('unsaved_children', {}) or {}

        instances_to_save = set([])

        accounts_to_reestimate = {}
        subaccounts_to_reestimate = {}
        for obj in instances:
            assert isinstance(obj, self.model)
            altered = obj.estimate(
                commit=False,
                trickle=False,
                unsaved_children=unsaved_children.get(obj.pk),
                **kwargs
            )
            if altered or obj.raw_value_changed:
                instances_to_save.add(obj)
            # The raw_value of the SubAccount is not calculated in the estimate
            # method, but does affect the nominal_value and will affect the
            # estimated values of parents - so we have to check if that changed
            # as well.x
            if (altered or obj.raw_value_changed or obj.was_just_added()) \
                    and obj.parent is not None:
                assert isinstance(
                    obj.parent, (self.model.account_cls(), self.model))
                if isinstance(obj.parent, self.model.account_cls()):
                    if obj.parent.pk in accounts_to_reestimate:
                        accounts_to_reestimate[obj.parent.pk]['unsaved'].add(obj)  # noqa
                    else:
                        accounts_to_reestimate[obj.parent.pk] = {
                            'instance': obj.parent,
                            'unsaved': set([obj])
                        }
                else:
                    if obj.parent.pk in subaccounts_to_reestimate:
                        subaccounts_to_reestimate[obj.parent.pk]['unsaved'].add(obj)  # noqa
                    else:
                        subaccounts_to_reestimate[obj.parent.pk] = {
                            'instance': obj.parent,
                            'unsaved': set([obj])
                        }
        budgets_to_reestimate = {}
        accounts = set([])
        for k, v in accounts_to_reestimate.items():
            obj = v['instance']
            altered = obj.estimate(
                commit=False,
                trickle=False,
                unsaved_children=v['unsaved'],
                **kwargs
            )
            if altered:
                accounts.add(obj)
            if (altered or obj.was_just_added()) and obj.parent is not None:
                if obj.parent.pk in budgets_to_reestimate:
                    budgets_to_reestimate[obj.parent.pk]['unsaved'].add(obj)
                else:
                    budgets_to_reestimate[obj.parent.pk] = {
                        'instance': obj.parent,
                        'unsaved': set([obj])
                    }

        budgets = set([])
        for k, v in budgets_to_reestimate.items():
            obj = v['instance']
            altered = obj.estimate(
                commit=False,
                unsaved_children=v['unsaved'],
                **kwargs
            )
            if altered:
                budgets.add(obj)

        if subaccounts_to_reestimate:
            s, a, b = self.bulk_estimate(
                instances=[
                    v['instance']
                    for _, v in subaccounts_to_reestimate.items()
                ],
                commit=False,
                unsaved_children={
                    v['instance'].pk: v['unsaved']
                    for _, v in subaccounts_to_reestimate.items()
                },
                **kwargs
            )
            instances_to_save = instances_to_save.union(s)
            accounts = accounts.union(a)
            budgets = budgets.union(b)

        if commit:
            self.bulk_update_post_estimation(instances_to_save)
            self.model.account_cls().objects.bulk_update_post_estimation(
                accounts)
            self.model.budget_cls().objects.bulk_update_post_estimation(budgets)
            return instances_to_save, accounts, budgets

        return instances_to_save, accounts, budgets


class TemplateSubAccountManager(SubAccountManager):
    pass


class BudgetSubAccountManager(SubAccountManager):

    @signals.disable()
    def bulk_calculate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)

        subaccounts, accounts, budgets = super().bulk_calculate(
            instances=instances,
            commit=False,
            **kwargs
        )
        actualized, accts, bgts = self.bulk_actualize(
            instances=instances,
            commit=False,
            **kwargs
        )
        subaccounts = subaccounts.union(actualized)
        accounts = accounts.union(accts)
        budgets = budgets.union(bgts)

        if commit:
            self.bulk_update_post_calculation(subaccounts)
            self.model.account_cls().objects.bulk_update_post_calculation(
                accounts)
            self.model.budget_cls().objects.bulk_update_post_calculation(
                budgets)
        return subaccounts, accounts, budgets

    @signals.disable()
    def bulk_actualize(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        unsaved_children = kwargs.pop('unsaved_children', {}) or {}

        instances_to_save = set([])

        accounts_to_reactualize = {}
        subaccounts_to_reactualize = {}
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
                    assert isinstance(obj.parent, (
                        self.model.account_cls(), self.model))
                    if isinstance(obj.parent, self.model.account_cls()):
                        if obj.parent.pk in accounts_to_reactualize:
                            accounts_to_reactualize[
                                            obj.parent.pk]['unsaved'].add(obj)
                        else:
                            accounts_to_reactualize[obj.parent.pk] = {
                                'instance': obj.parent,
                                'unsaved': set([obj])
                            }
                    else:
                        if obj.parent.pk in subaccounts_to_reactualize:
                            subaccounts_to_reactualize[
                                            obj.parent.pk]['unsaved'].add(obj)
                        else:
                            subaccounts_to_reactualize[obj.parent.pk] = {
                                'instance': obj.parent,
                                'unsaved': set([obj])
                            }

        budgets_to_reactualize = {}
        accounts = set([])
        for k, v in accounts_to_reactualize.items():
            obj = v['instance']
            altered = obj.actualize(
                commit=False,
                trickle=False,
                unsaved_children=v['unsaved'],
                **kwargs
            )
            if altered:
                accounts.add(obj)
            if (altered or obj.was_just_added()) and obj.parent is not None:
                if obj.parent.pk in budgets_to_reactualize:
                    budgets_to_reactualize[obj.parent.pk]['unsaved'].add(obj)
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

        if subaccounts_to_reactualize:
            s, a, b = self.bulk_actualize(
                instances=[
                    v['instance']
                    for _, v in subaccounts_to_reactualize.items()
                ],
                commit=False,
                unsaved_children={
                    v['instance'].pk: v['unsaved']
                    for _, v in subaccounts_to_reactualize.items()
                },
                **kwargs
            )
            instances_to_save = instances_to_save.union(s)
            accounts = accounts.union(a)
            budgets = budgets.union(b)

        if commit:
            self.bulk_update_post_actualization(instances_to_save)
            self.model.account_cls().objects.bulk_update_post_actualization(
                accounts)
            self.model.budget_cls().objects.bulk_update_post_actualization(
                budgets)

        return instances_to_save, accounts, budgets

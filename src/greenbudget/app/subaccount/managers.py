from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, Q, When, Value as V, BooleanField

from polymorphic.managers import PolymorphicManager

from greenbudget.lib.utils import concat, set_or_list
from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet

from greenbudget.app import signals
from greenbudget.app.budgeting.query import (
    BaseBudgetQuerier, BudgetQuerier, TemplateQuerier)


class SubAccountQuerierMixin:
    @signals.disable()
    def bulk_delete(self, instances):
        groups = [obj.group for obj in instances if obj.group is not None]

        for obj in instances:
            obj.invalidate_caches(trickle=True)
            obj.delete()

        self.bulk_calculate_all([obj.parent for obj in instances])
        self.bulk_delete_empty_groups(groups)

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was recalculated.
        for budget in set([inst.budget for inst in instances]):
            budget.mark_updated()

    @signals.disable()
    def bulk_add(self, instances):
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
    def bulk_save(self, instances, update_fields):
        calculated, accounts, budgets = self.bulk_calculate(
            instances, commit=False)
        instances = calculated.union(instances)
        groups = [obj.group for obj in instances if obj.group is not None]

        # Note: This will more than likely lead to invalidating caches multiple
        # times due to the children invalidating parent caches.  We need to
        # investigate batch catch invalidation with Django/AWS.
        for obj in set_or_list(instances) + set_or_list(budgets) \
                + set_or_list(accounts):
            obj.invalidate_caches(trickle=True)
            if obj.children.count() != 0 and isinstance(obj, self.model):
                obj.clear_deriving_fields(commit=False)

        self.bulk_update(
            instances,
            tuple(self.model.CALCULATED_FIELDS) + tuple(update_fields)
        )
        self.account_cls.objects.bulk_update_post_calculation(accounts)
        self.base_cls.objects.bulk_update_post_calculation(budgets)

        self.bulk_delete_empty_groups(groups)

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was recalculated.
        for budget in set([inst.budget for inst in instances]):
            budget.mark_updated()

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
                    obj.parent, (self.account_cls, self.model))
                if isinstance(obj.parent, self.account_cls):
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
            self.account_cls.objects.bulk_update_post_estimation(accounts)
            self.base_cls.objects.bulk_update_post_estimation(budgets)
            return instances_to_save, accounts, budgets

        return instances_to_save, accounts, budgets

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
            for account in self.account_cls.objects.filter(parent=budget)
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
        account_ct = ContentType.objects.get_for_model(self.account_cls)
        subaccount_ct = ContentType.objects.get_for_model(self.subaccount_cls)
        accounts = [
            q[0] for q in self.account_cls.objects.filter(parent=budget)
            .only('pk').values_list('pk')
        ]
        query = Q(content_type_id=account_ct) & Q(object_id__in=accounts)
        subaccount_levels = self._get_subaccount_levels(budget)
        for level in subaccount_levels:
            query = query | (
                Q(content_type_id=subaccount_ct) & Q(object_id__in=level))
        return query


class SubAccountQuerier(SubAccountQuerierMixin, BaseBudgetQuerier):
    pass


class SubAccountQuery(SubAccountQuerier, BulkCreatePolymorphicQuerySet):
    pass


class SubAccountManager(SubAccountQuerier, PolymorphicManager):
    queryset_class = SubAccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class TemplateSubAccountQuerier(SubAccountQuerierMixin, TemplateQuerier):
    pass


class TemplateSubAccountQuery(
        TemplateSubAccountQuerier, BulkCreatePolymorphicQuerySet):
    pass


class TemplateSubAccountManager(TemplateSubAccountQuerier, PolymorphicManager):
    queryset_class = TemplateSubAccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetSubAccountQuerier(SubAccountQuerierMixin, BudgetQuerier):
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
            self.account_cls.objects.bulk_update_post_calculation(accounts)
            self.budget_cls.objects.bulk_update_post_calculation(budgets)
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
                    assert isinstance(obj.parent, (self.account_cls, self.model))
                    if isinstance(obj.parent, self.account_cls):
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
            self.account_cls.objects.bulk_update_post_actualization(accounts)
            self.budget_cls.objects.bulk_update_post_actualization(budgets)

        return instances_to_save, accounts, budgets


class BudgetSubAccountQuery(
        BudgetSubAccountQuerier, BulkCreatePolymorphicQuerySet):
    pass


class BudgetSubAccountManager(BudgetSubAccountQuerier, PolymorphicManager):
    queryset_class = BudgetSubAccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

import collections

from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, Q, When, Value as V, BooleanField

from greenbudget.lib.utils import concat, ensure_iterable

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_actuals_owners_cache
from greenbudget.app.budgeting.managers import (
    BudgetingPolymorphicOrderedRowManager)
from greenbudget.app.budgeting.utils import BudgetTree
from greenbudget.app.tabling.query import (
    OrderedRowQuerier, OrderedRowPolymorphicQuerySet)

from .cache import (
    subaccount_instance_cache,
    invalidate_parent_instance_cache,
    invalidate_parent_children_cache,
    invalidate_parent_groups_cache
)


MAX_UNIQUE_CONSTRAINT_RECURSIONS = 1


class SubAccountQuerier(OrderedRowQuerier):

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
            _has_budget=Case(
                When(self._get_budget_query(budget), then=V(True)),
                default=V(False),
                output_field=BooleanField()
            )
        ).filter(_has_budget=True)

    def _get_subaccount_levels(self, budget):
        subaccount_levels = []
        subaccounts = concat([
            [q[0] for q in account.children.only('pk').values_list('pk')]
            for account in budget.account_cls.objects.filter(parent=budget)
        ])
        while len(subaccounts) != 0:
            subaccount_levels.append(subaccounts)
            subaccounts = concat([
                [q[0] for q in account.children.only('pk').values_list('pk')]
                for account in self.model.objects
                .prefetch_related('children').filter(id__in=subaccounts)
            ])
        return subaccount_levels

    def _get_budget_query(self, budget):
        account_ct = ContentType.objects.get_for_model(budget.account_cls)
        subaccount_ct = ContentType.objects.get_for_model(
            budget.subaccount_cls)
        accounts = [
            q[0] for q in budget.account_cls.objects.filter(parent=budget)
            .only('pk').values_list('pk')
        ]
        query = Q(content_type_id=account_ct) & Q(object_id__in=accounts)
        subaccount_levels = self._get_subaccount_levels(budget)
        for level in subaccount_levels:
            query = query | (
                Q(content_type_id=subaccount_ct) & Q(object_id__in=level))
        return query


class SubAccountQuerySet(
        SubAccountQuerier, OrderedRowPolymorphicQuerySet):
    pass


class SubAccountManager(
        SubAccountQuerier, BudgetingPolymorphicOrderedRowManager):
    queryset_class = SubAccountQuerySet

    def bulk_update(self, instances, fields, **kwargs):
        """
        Due to the recursive nature of a :obj:`SubAccount`, in the sense that
        the :obj:`SubAccount` can be a parent of another :obj:`SubAccount`, if
        we bulk update a series of :obj:`SubAccount`(s) where given instances
        are referential to other instances in the series, we will run into
        database transaction locks with the self-referential Foreign Keys.

        To avoid this, we have to update the :obj:`SubAccount`(s) one level
        at a time - starting from the bottom of the tree and working its way
        upwards.
        """
        updated = 0
        for _, subaccounts in self.group_by_nested_level(instances):
            updated += super().bulk_update(subaccounts, fields, **kwargs)
        return updated

    def group_by_nested_level(self, instances, reverse=True):
        """
        Groups the provided :obj:`SubAccount`(s) by the level they exist at
        in the budget ancestry tree.

        Instances of :obj:`SubAccount`(s) are self-referential, meaning that
        they can have parent/child relationships with the same model.  When
        updating entities in the budget ancestry tree, we need to treat each
        :obj:`SubAccount` level of the tree in isolation.
        """
        grouped = collections.defaultdict(list)
        # We cannot cast the iterable as a set because the models may or may
        # not have been saved yet, and if they haven't been saved they do not
        # have a PK - which means they are not hashable, so we have to assume
        # the instances provided to this method are unique in that case.
        for instance in ensure_iterable(instances, cast=list):
            if (hasattr(instance, 'pk')
                    and instance not in grouped[instance.nested_level]) \
                    or not hasattr(instance, 'pk'):
                grouped[instance.nested_level].append(instance)
        return sorted(
            list(grouped.items()), key=lambda tup: tup[0], reverse=reverse)

    @signals.disable()
    def bulk_delete(self, instances, request=None):
        groups = [obj.group for obj in instances if obj.group is not None]
        budgets = set([inst.budget for inst in instances])

        # We must invalidate the caches before the delete is performed so
        # we still have access to the PKs.
        subaccount_instance_cache.invalidate(instances)
        budget_actuals_owners_cache.invalidate(budgets)

        parents = set([s.parent for s in instances])
        invalidate_parent_groups_cache(parents)

        for obj in instances:
            obj.delete()

        self.bulk_calculate_all([
            obj.parent for obj in
            [i for i in instances
            if i.will_change_parent_estimation(i.actions.DELETE)]
        ])
        self.bulk_delete_empty_groups(groups)
        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(budgets, request.user)

    @signals.disable()
    def bulk_add(self, instances, request=None):
        created = self.bulk_create(instances, return_created_objects=True)

        budget_actuals_owners_cache.invalidate(created)
        parents = set([p.parent for p in created])
        invalidate_parent_children_cache(parents)
        invalidate_parent_instance_cache(parents)
        invalidate_parent_groups_cache(parents)

        # When creating SubAccount(s), the only way that they have an estimated
        # value and affect the parent's estimated value will be if the rate and
        # quantity field are non-null.  This is because a SubAccount cannot be
        # assigned children, markups or fringes until after it is created.
        # Furthermore, the SubAccount will only have an actual value and affect
        # the parent's actual value if the SubAccount has been assigned Actual
        # instances, which cannot be done until after the SubAccount is created.
        self.bulk_calculate([
            i for i in created
            if i.will_change_parent_estimation(i.actions.CREATE)
        ])
        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(created, request.user)
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields, request=None):
        instances = ensure_iterable(instances)
        # The estimation is only concerned with looking at the children of the
        # SubAccount, and when we are bulk updating SubAccount(s) we cannot
        # alter the children since it is a reverse FK field.  Furthermore, the
        # actual value cannot change via a bulk update, so the only way that
        # the instance is recalculated is if the SubAccount has no children and
        # the rate, quantity or multiplier field has changed.
        tree = self.bulk_calculate(
            [i for i in instances if i.will_change_parent_estimation(
                i.actions.UPDATE)],
            commit=False,
        )

        instances = tree.subaccounts.union(instances)
        subaccount_instance_cache.invalidate(instances)

        parents = set([s.parent for s in instances])
        invalidate_parent_groups_cache(parents)

        groups = [obj.group for obj in instances if obj.group is not None]

        self.bulk_update(
            instances,
            tuple(self.model.CALCULATED_FIELDS) + tuple(update_fields)
        )
        self.model.account_cls.objects.bulk_update_post_calc(tree.accounts)
        self.model.budget_cls.objects.bulk_update_post_calc(tree.budgets)

        self.bulk_delete_empty_groups(groups)
        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(instances, request.user)

    @signals.disable()
    def bulk_calculate(self, *args, **kwargs):
        return self.bulk_estimate(*args, **kwargs)

    def _subaccounts_recursion(self, tree, method_name, **kwargs):
        pass_up_kwargs = dict(**kwargs, **{'commit': False, 'trickle': False})

        def recursion(subaccounts, unsaved=None):
            unsaved = unsaved or {}
            # Since SubAccount(s) can be self-referential, and children affect
            # the parents, we need to incrementally work our way up from the
            # lowest level of SubAccount(s) to the highest level of
            # SubAccount(s).
            for _, subs_at_level in self.group_by_nested_level(subaccounts):
                altered_subaccounts = []
                for obj in subs_at_level:
                    altered = getattr(obj, method_name)(
                        unsaved_children=unsaved.get(obj.pk),
                        **pass_up_kwargs
                    )

                    if altered:
                        tree.add(obj.parent)
                        altered_subaccounts.append(obj)

                        # This is why this method has to be recursive - when
                        # reestimating the SubAccount(s) at a given level, it
                        # might lead to the requirement to reestimate a parent
                        # SubAccount at the next level up.
                        if isinstance(obj.parent, self.model):
                            subaccounts.add(obj.parent)

                # Add the altered SubAccount(s) to the tree of objects that have
                # to be saved after the routine.
                tree.add(altered_subaccounts)
                # Remove the SubAccount(s) we just itereated through from the
                # filtration so we do not iterate through them in the next
                # recursion.
                subaccounts = subaccounts.difference(set(subs_at_level))
                # Update the unsaved children for either the next level up of
                # the SubAccount recursion or the Account level if we reached
                # the highest SubAccount level in the tree.
                unsaved_children = self.group_by_parents(altered_subaccounts)

            return subaccounts, unsaved_children
        return recursion

    def perform_bulk_routine(self, instances, method_name, **kwargs):
        instances = ensure_iterable(instances)
        unsaved = kwargs.pop('unsaved_children', {}) or {}

        tree = BudgetTree()

        pass_up_kwargs = dict(**kwargs, **{'commit': False, 'trickle': False})
        recursive_method = self._subaccounts_recursion(
            tree, method_name, **kwargs)

        # Continue to work our way up the SubAccount levels of the budget
        # ancestry tree until we reach the Account level - at which point the
        # filtration will be empty.
        filtration = set(instances)
        while filtration:
            filtration, unsaved = recursive_method(filtration, unsaved=unsaved)

        altered_accounts = []
        for obj in tree.accounts:
            altered = getattr(obj, method_name)(
                unsaved_children=unsaved.get(obj.pk),
                **pass_up_kwargs
            )
            if altered or obj.was_just_added():
                altered_accounts.append(obj)
                tree.add(obj.parent)

        tree.add(altered_accounts)
        unsaved = self.group_by_parents(altered_accounts)

        for obj in tree.budgets:
            altered = getattr(obj, method_name)(
                unsaved_children=unsaved.get(obj.pk),
                **pass_up_kwargs
            )
            if altered:
                tree.add(obj)
        return tree

    @signals.disable()
    def bulk_estimate(self, instances, **kwargs):
        instances = ensure_iterable(instances)
        commit = kwargs.pop('commit', True)
        tree = self.perform_bulk_routine(
            instances=instances,
            method_name='estimate',
            **kwargs
        )
        if commit:
            self.bulk_update_post_est(tree.subaccounts)
            self.model.account_cls.objects.bulk_update_post_est(tree.accounts)
            self.model.budget_cls.objects.bulk_update_post_est(tree.budgets)
        return tree


class TemplateSubAccountManager(SubAccountManager):
    pass


class BudgetSubAccountManager(SubAccountManager):

    @signals.disable()
    def bulk_calculate(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        tree = super().bulk_calculate(instances, commit=False, **kwargs)
        actualized_tree = self.bulk_actualize(instances, commit=False, **kwargs)
        tree.merge(actualized_tree)
        if commit:
            self.bulk_update_post_calc(tree.subaccounts)
            self.model.account_cls.objects.bulk_update_post_calc(tree.accounts)
            self.model.budget_cls.objects.bulk_update_post_calc(tree.budgets)
        return tree

    @signals.disable()
    def bulk_actualize(self, instances, **kwargs):
        instances = ensure_iterable(instances)
        commit = kwargs.pop('commit', True)
        tree = self.perform_bulk_routine(
            instances=instances,
            method_name='actualize',
            **kwargs
        )
        if commit:
            self.bulk_update_post_act(tree.subaccounts)
            self.model.account_cls.objects.bulk_update_post_act(tree.accounts)
            self.model.budget_cls.objects.bulk_update_post_act(tree.budgets)
        return tree

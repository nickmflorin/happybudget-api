import collections
import datetime
import logging

from happybudget.lib.utils import ensure_iterable

from happybudget.app import signals, query, managers
from happybudget.app.tabling.managers import OrderedRowManagerMixin
from happybudget.app.tabling.query import (
    OrderedRowPolymorphicQuerySet, OrderedRowQuerySet, RowQuerySet,
    RowQuerier)

from .cache import invalidate_groups_cache
from .utils import BudgetTree


logger = logging.getLogger('happybudget')


class BudgetingManagerMixin:
    def validate_before_save(self, instances):
        for instance in instances:
            instance.validate_before_save()

    def bulk_update(self, instances, fields, **kwargs):
        self.validate_before_save(instances)
        return super().bulk_update(instances, fields, **kwargs)

    def bulk_create(self, instances, **kwargs):
        self.validate_before_save(instances)
        return super().bulk_create(instances, **kwargs)

    def bulk_update_post_calc(self, instances, **kwargs):
        if instances:
            return self.bulk_update(
                instances,
                fields=self.model.CALCULATED_FIELDS,
                **kwargs
            )
        return None

    def bulk_update_post_est(self, instances, **kwargs):
        if instances:
            return self.bulk_update(
                instances,
                fields=self.model.ESTIMATED_FIELDS,
                **kwargs
            )
        return None

    def bulk_update_post_act(self, instances, **kwargs):
        if instances:
            return self.bulk_update(instances, fields=['actual'], **kwargs)
        return None

    def mark_budgets_updated(self, instances, user):
        """
        Marks the series of :obj:`Budget` or :obj:`Template` instances as having
        been updated at the current time by the provided :obj:`User`.  The
        series of :obj:`Budget` or :obj:`Template` instances can be provided
        either as the :obj:`Budget` or :obj:`Template` instances themselves or
        any instance that has a `budget` field pointing to the related
        :obj:`Budget` or :obj:`Template` instance.

        Note:
        ----
        In regard to the `updated_at` and `updated_by` fields on a :obj:`Budget`
        or :obj:`Template` there are two things that we need to be aware of:

        (1) Usage of `auto_now` on Django Fields

        The `auto_now` attribute of the `updated_at` field for a :obj:`Budget`
        or :obj:`Template` does not automatically update when instances of
        :obj:`Budget` or :obj:`Template` are bulk updated or bulk created, only
        when they are created or updated one instance at a time outside the
        bulk operation methods inherently built in via Django's model managers.

        (2) Related Models of :obj:`Budget` or :obj:`Template`

        There are times when we are creating, deleting or updating models that
        are related to the :obj:`Budget` or :obj:`Template` but will not trigger
        a save of the :obj:`Budget` or :obj:`Template` itself, because they
        are separate models.

        Because of these two considerations, we have to explicitly update the
        `updated_at` and `updated_by` fields when performing operations on
        models related to a :obj:`Budget` or :obj:`Template` in a bulk context.
        """
        # pylint: disable=import-outside-toplevel
        from happybudget.app.budget.models import BaseBudget
        budgets = set([])
        for instance in instances:
            assert isinstance(instance, BaseBudget) \
                or hasattr(instance, 'budget'), \
                f"The model class {instance.__class__} does not have a " \
                "`budget` field, so the instances provided to the method " \
                f"must all be of type {type(BaseBudget)}."
            if isinstance(instance, BaseBudget):
                budgets.add(instance.pk)
            else:
                budgets.add(getattr(instance, 'budget').pk)

        self.model.budget_cls.objects.filter(pk__in=budgets).update(
            updated_at=datetime.datetime.now().replace(
                tzinfo=datetime.timezone.utc),
            updated_by=user
        )

    @signals.disable()
    def bulk_delete_empty_groups(self, groups):
        """
        Deletes provided :obj:`Group` instances that no longer have any children
        as a result of a change in assignment.

        When the :obj:`Group` that is optionally assigned to an :obj:`Account`
        or :obj:`SubAccount` changes, if the :obj:`Account` or :obj:`SubAccount`
        was previously assigned a :obj:`Group` that :obj:`Group` effectively
        loses a child.  If the :obj:`Group` loses a child in this manner, there
        is the possibility that the :obj:`Group` no longer has children - if that
        :obj:`Account` or :obj:`SubAccount` was previously it's only child, and
        thus should be deleted.

        This behavior is encapsulated by the
        :obj:`happybudget.app.group.signals.delete_empty_group` signal receiver,
        but this method is meant to be used in the case of bulk operations which
        do not fire signals.
        """
        # pylint: disable=import-outside-toplevel
        from happybudget.app.group.models import Group
        groups_to_delete = set([])

        for group in groups:
            group_id = group if not isinstance(group, Group) else group.pk
            if self.model.objects.filter(group_id=group_id).count() == 0:
                group = Group.objects.get(pk=group_id)
                logger.info(
                    "Deleting group %s after it was removed from %s "
                    "because the group no longer has any children."
                    % (
                        group_id,
                        self.model.__class__.__name__,
                    )
                )
                groups_to_delete.add(group)

        group_parents = set([g.parent for g in groups_to_delete])
        invalidate_groups_cache(group_parents)
        # We do not want to include information about the :obj:`User`
        # associated with the current request since these deletes are for
        # general maintenance purposes - not an explicit action by a
        # :obj:`User`.
        Group.objects.filter(pk__in=[g.pk for g in groups_to_delete]) \
            .delete(force_ignore_signal_user=True)

    def group_by_parents(self, instances):
        """
        Groups the provided instances by their parent, returning an
        :obj:`collections.defaultdict` instance indexed by the primary keys
        of the distinct parents and valued by the list of instances in the
        provided set that have that distinct parent.
        """
        grouped = collections.defaultdict(list)
        for obj in instances:
            grouped[obj.parent.pk].append(obj)
        return grouped

    def perform_filtration_routines(self, filtration, routine_method, **kwargs):
        """
        Performs the filtration routines for a given routine method, whether it
        be actualization, estimation or calculation, on the provided instances,
        which can consist of instances of :obj:`Account`, :obj:`BaseBudget`,
        and :obj:`SubAccount`.

        This method allows us to reestimate, reactualize or recalculate any
        number of instances belonging to any number of :obj:`Budget`(s), such
        that we are performing the estimation, actualization or calculation
        logic the minimum number of times and saving the entities to the
        database - the minimum number of times, which is obviously a large
        performance boost.

        The routine methodology behaves like a filtration, starting at the
        lowest point of the :obj:`BaseBudget` ancestry tree and working its way
        upwards, keeping track of every entity in the tree that needs to be
        either reactualized, reestimated or recalculated (depending on the
        specific `routine_method`) as a result of any values of it's children
        changing that contribute to the values of it's parent.

        Consider the definition of the budget ancestry tree to be the tree
        that is constructed from the parent/child relationships amongst the
        entities of a :obj:`Budget` or :obj:`Template`:

        - Budget/Template
            - Account
                - SubAccount (Recursive)
                    - SubAccount
                - SubAccount
                - SubAccount
            - Account
                - SubAccount (Recursive)
                    - SubAccount
                    - SubAccount
            - Account

        For each level of the tree that the provided instances instances exist
        in, the filtration will start at the base level and work it's way
        upwards, keeping track of the entities that need to be saved due to
        a reestimated, recalculated or reactualized value either as a result of
        it's children changing or as a result of the instance being in the set
        of provided instances that explicitly warrants the reestimation,
        recalculation or reactualization.

        Then, after all entities in the provided instances and entities that are
        parents (at any level) in the tree of the provided instances have been
        reesetimated, reactualized or recalculated - they are all saved in a
        batch.

        Level 0: [SubAccount]
            Since the SubAccount level of the ancestry tree is recursive, the
            parent of each :obj:`SubAccount` or :obj:`Markup` can either
            be a :obj:`SubAccount` or a :obj:`Account`.

            Parents: [Account, SubAccount]

        ...

        Level n: [Account]
            Parents: [Budget]

        Level n + 1: [Budget]
            Parents: None
        """
        tree = BudgetTree()

        methods = {}
        if isinstance(routine_method, dict):
            methods = routine_method
        else:
            methods = {
                'subaccount': getattr(
                    self.model.subaccount_cls.objects, routine_method),
                'account': getattr(
                    self.model.account_cls.objects, routine_method),
                'budget': getattr(
                    self.model.budget_cls.objects, routine_method)
            }

        # An array of tuples, where each tuple represents the nested level and
        # the SubAccount(s) at that level, ordered by the nested level moving
        # upwards in the ancestry tree.  This allows us to address the recursive
        # nature of the SubAccount levels of the tree, ensuring that we only
        # apply logic to the parents after all it's children have been addressed.
        grouped = self.model.subaccount_cls.objects.group_by_nested_level(
            filtration.subaccounts)

        # Initially, there are no unsaved children - because no children have
        # been reestimated, reactualized or recalculated just yet.
        unsaved_children = {}
        for _, subs_at_level in grouped:
            # The instances in the returned tree will be only those that have
            # changed in the tree as a result of the logic being applied to the
            # children.
            sub_tree = methods['subaccount'](
                # If the logic was already applied to the SubAccount as a result
                # of applying the logic to a child of the SubAccount, do not
                # reapply the logic.
                instances=[
                    s for s in subs_at_level
                    if s in filtration.subaccounts
                ],
                commit=False,
                unsaved_children=unsaved_children,
                **kwargs
            )
            # Since we are saving all of the instances at the end, we need to
            # to provide the unsaved children to the logic at each level of the
            # tree such that the logic is applied to the parent nodes accounting
            # for unsaved changes to the children nodes.
            unsaved_children = self.group_by_parents(sub_tree.subaccounts)
            tree.merge(sub_tree)

            # The logic has been applied to all entities in the tree, so they
            # can be removed from the set of ongoing entities requiring
            # application of the logic.
            filtration.difference(sub_tree)

        # The instances in the returned tree will be only those that have
        # changed in the tree as a result of the logic being applied to the
        # children.
        account_tree = methods['account'](
            instances=filtration.accounts,
            commit=False,
            unsaved_children=unsaved_children,
            **kwargs
        )
        tree.merge(account_tree)

        # The logic has been applied to all entities in the tree, so they
        # can be removed from the set of ongoing entities requiring
        # application of the logic.
        filtration.difference(account_tree)

        # The instances in the returned tree will be only those that have
        # changed in the tree as a result of the logic being applied to the
        # children.
        budget_tree = methods['budget'](
            instances=filtration.budgets,
            commit=False,
            unsaved_children=self.group_by_parents(tree.accounts),
            **kwargs
        )
        tree.merge(budget_tree)

        # The logic has been applied to all entities in the tree, so they
        # can be removed from the set of ongoing entities requiring
        # application of the logic.
        filtration.difference(budget_tree)

        # At this point, the filtration should be entirely empty - since we
        # have traversed any and all paths of the tree for each instance in
        # the original filtration.
        return tree

    @signals.disable()
    def bulk_estimate_all(self, instances, **kwargs):
        """
        Performs the estimation routines on the provided instances, which
        can consist of instances of :obj:`Account`, :obj:`BaseBudget`,
        and :obj:`SubAccount`.
        """
        commit = kwargs.pop('commit', True)
        accounts = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.account_cls)
        ])
        budgets = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.budget_cls)
        ])
        # This set represents all SubAccount(s), regardless of where they are
        # in the ancestry tree.  This means that SubAccount(s) will be in this
        # list along with the SubAccount they they may be children of.  Since
        # metrics of the children affect the metrics of the parent, which is how
        # this method works, we have to incrementally work our way upwards, from
        # the SubAccount(s) at the lowest levels of the tree to the SubAccount(s)
        # at the highest levels of the tree.  Otherwise, we would be potentially
        # reestimating a parent SubAccount pre-emptively, before it's children
        # were reestimated.
        subaccounts = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.subaccount_cls)
        ])
        tree = self.perform_filtration_routines(
            filtration=BudgetTree(
                accounts=accounts,
                subaccounts=subaccounts,
                budgets=budgets
            ),
            routine_method='bulk_estimate',
            **kwargs
        )
        if commit:
            self.model.subaccount_cls.objects.bulk_update_post_est(
                tree.subaccounts)
            self.model.account_cls.objects.bulk_update_post_est(tree.accounts)
            self.model.budget_cls.objects.bulk_update_post_est(tree.budgets)
        return tree

    @signals.disable()
    def bulk_actualize_all(self, instances, **kwargs):
        """
        Performs the actualization routines on the provided instances, which
        can consist of instances of :obj:`BudgetAccount`, :obj:`Budget`,
        :obj:`Markup` and :obj:`BudgetSubAccount`.
        """
        # pylint: disable=import-outside-toplevel
        from happybudget.app.account.models import BudgetAccount
        from happybudget.app.budget.models import Budget
        from happybudget.app.markup.models import Markup
        from happybudget.app.subaccount.models import BudgetSubAccount

        assert all([
            obj.domain == "budget"
            for obj in ensure_iterable(instances)
        ]), "Actualization is only applicable for the budget domain."

        commit = kwargs.pop('commit', True)
        markups = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, Markup)
        ])
        accounts = set([
            obj for obj in ensure_iterable(instances)
            + [m.parent for m in markups]
            if isinstance(obj, BudgetAccount)
        ])
        budgets = set([
            obj for obj in ensure_iterable(instances)
            + [m.parent for m in markups]
            if isinstance(obj, Budget)
        ])
        # This set represents all SubAccount(s), regardless of where they are
        # in the ancestry tree.  This means that SubAccount(s) will be in this
        # list along with the SubAccount they they may be children of.  Since
        # metrics of the children affect the metrics of the parent, which is
        # how this method works, we have to incrementally work our way upwards,
        # from the SubAccount(s) at the lowest levels of the tree to the
        # SubAccount(s) at the highest levels of the tree.  Otherwise, we would
        # be potentially reestimating a parent SubAccount pre-emptively, before
        # it's children were reestimated.
        subaccounts = set([
            obj for obj in ensure_iterable(instances)
            # If an Actual is associated with a Markup instance, the parent of
            # that Markup instance must be reactualized - we do not have to
            # reactualize the Markup itself because it's actual value is derived
            # from an @property.
            + [m.parent for m in markups]
            if isinstance(obj, BudgetSubAccount)
        ])
        tree = self.perform_filtration_routines(
            filtration=BudgetTree(
                accounts=accounts,
                subaccounts=subaccounts,
                budgets=budgets
            ),
            routine_method={
                'account': BudgetAccount.objects.bulk_actualize,
                'subaccount': BudgetSubAccount.objects.bulk_actualize,
                'budget': Budget.objects.bulk_actualize,
            },
            **kwargs
        )
        if commit:
            BudgetSubAccount.objects.bulk_update_post_act(tree.subaccounts)
            BudgetAccount.objects.bulk_update_post_act(tree.accounts)
            Budget.objects.bulk_update_post_act(tree.budgets)

        return tree

    @signals.disable()
    def bulk_calculate_all(self, instances, **kwargs):
        """
        Performs both the estimation and actualization (if applicable) routines
        on the provided instances, which can consist of instances of
        :obj:`Account`, :obj:`BaseBudget`, :obj:`Markup` and :obj:`SubAccount`.
        """
        # pylint: disable=import-outside-toplevel
        from happybudget.app.markup.models import Markup

        commit = kwargs.pop('commit', True)
        markups = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, Markup)
        ])
        accounts = set([
            obj for obj in ensure_iterable(instances)
            + [m.parent for m in markups]
            if isinstance(obj, self.model.account_cls)
        ])
        budgets = set([
            obj for obj in ensure_iterable(instances)
            + [m.parent for m in markups]
            if isinstance(obj, self.model.budget_cls)
        ])
        subaccounts = set([
            obj for obj in ensure_iterable(instances)
            # If an Actual is associated with a Markup instance, the parent of
            # that Markup instance must be reactualized - we do not have to
            # reactualize the Markup itself because it's actual value is derived
            # from an @property.
            + [m.parent for m in markups]
            if isinstance(obj, self.model.subaccount_cls)
        ])
        tree = self.perform_filtration_routines(
            filtration=BudgetTree(
                accounts=accounts,
                subaccounts=subaccounts,
                budgets=budgets
            ),
            routine_method='bulk_calculate',
            **kwargs
        )
        if commit:
            self.model.subaccount_cls.objects.bulk_update_post_calc(
                tree.subaccounts)
            self.model.account_cls.objects.bulk_update_post_calc(tree.accounts)
            self.model.budget_cls.objects.bulk_update_post_calc(tree.budgets)
        return tree


class BudgetingManager(BudgetingManagerMixin, managers.Manager):
    queryset_class = query.QuerySet


class BudgetingRowManager(
        RowQuerier, BudgetingManagerMixin, managers.Manager):
    queryset_class = RowQuerySet


class BudgetingOrderedRowManager(OrderedRowManagerMixin, BudgetingRowManager):
    queryset_class = OrderedRowQuerySet


class BudgetingPolymorphicManager(
        BudgetingManagerMixin, managers.PolymorphicManager):
    pass


class BudgetingPolymorphicOrderedRowManager(
        BudgetingOrderedRowManager, managers.PolymorphicManager):
    queryset_class = OrderedRowPolymorphicQuerySet

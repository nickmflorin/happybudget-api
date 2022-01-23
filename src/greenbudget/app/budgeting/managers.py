import logging

from django.db import models
from polymorphic.models import PolymorphicManager

from greenbudget.lib.utils import ensure_iterable
from greenbudget.lib.django_utils.models import (
    PrePKBulkCreateQuerySet,
    BulkCreatePolymorphicQuerySet
)

from greenbudget.app import signals
from greenbudget.app.tabling.managers import RowManagerMixin
from greenbudget.app.tabling.query import RowPolymorphicQuerySet, RowQuerySet


logger = logging.getLogger('greenbudget')


class BudgetingManagerMixin:
    def mark_budgets(self, instances=None, budgets=None):
        assert budgets is not None or instances is not None, \
            "Must either provide the budgets or instances."
        if budgets is None:
            budgets = set([inst.budget for inst in instances])
        for budget in budgets:
            budget.mark_updated()

    def validate_before_save(self, instances):
        for instance in instances:
            if hasattr(instance, 'validate_before_save'):
                instance.validate_before_save(bulk_context=True)

    def bulk_update(self, instances, fields, mark_budgets=True, **kwargs):
        self.validate_before_save(instances)
        results = super().bulk_update(instances, fields, **kwargs)
        self.cleanup(instances, mark_budgets=mark_budgets)
        return results

    def bulk_create(self, instances, mark_budgets=True, **kwargs):
        self.validate_before_save(instances)
        results = super().bulk_create(instances, **kwargs)
        self.cleanup(instances, mark_budgets=mark_budgets)
        return results

    def cleanup(self, instances, **kwargs):
        for instance in instances:
            # Not all of the models that use these managers will have the
            # CacheControlMixin.
            if hasattr(instance, 'CACHES'):
                instance.invalidate_caches(["detail"])
                if hasattr(instance, 'parent'):
                    instance.parent.invalidate_caches(["detail", "children"])

    def bulk_update_post_calculation(self, instances, **kwargs):
        if instances:
            return self.bulk_update(
                instances=instances,
                fields=self.model.CALCULATED_FIELDS,
                **kwargs
            )
        return None

    def bulk_update_post_estimation(self, instances, **kwargs):
        if instances:
            return self.bulk_update(
                instances=instances,
                fields=self.model.ESTIMATED_FIELDS,
                **kwargs
            )
        return None

    def bulk_update_post_actualization(self, instances, **kwargs):
        if instances:
            return self.bulk_update(
                instances=instances,
                fields=['actual'],
                **kwargs
            )
        return None

    @signals.disable()
    def bulk_delete_empty_groups(self, groups):
        from greenbudget.app.group.models import Group

        for group in groups:
            id = group if not isinstance(group, Group) else group.pk
            if self.model.objects.filter(group_id=id).count() == 0:
                try:
                    Group.objects.get(pk=id).delete()
                    logger.info(
                        "Deleting group %s after it was removed from %s "
                        "because the group no longer has any children."
                        % (
                            id,
                            self.model.__class__.__name__,
                        )
                    )
                except Group.DoesNotExist:
                    # We have to be concerned with race conditions here.
                    pass

    @signals.disable()
    def bulk_estimate_all(self, instances, **kwargs):
        """
        Performs the estimation routines on the provided instances, which
        can consist of instances of :obj:`Account`, :obj:`BaseBudget`,
        :obj:`Markup` and :obj:`SubAccount`.

        The estimation methodology behaves like a filtration, starting
        at the lowest point of the budget ancestry tree and working it's
        way upwards, keeping track of every entity that needs to be
        reestimated as a result of any values of one of it's children that
        contribute to the estimation changing.

        Consider the definition of the budget ancestry tree to be the tree
        that is constructed from the parent/child relationships amongst the
        entities of a :obj:`Budget` or :obj:`Template`:

        - Budget/Template
            - Account
                - SubAccount
                    - SubAccount
                    - Markup
                - SubAccount
                - SubAccount
                - Markup
                - Markup
            - Account
                - SubAccount
                    - SubAccount
                    - SubAccount
                - Markup
            - Account
            - Markup

        The filtration starts at the lowest level of the tree, which consists
        of :obj:`SubAccount`(s) and :obj:`Markup`(s).  Each entity in the lowest
        level of the tree is reestimated.  If it is determined that any of the
        values that contribute to the parent's estimation have changed, then
        we must also reestimate the parent.  So the parent is added to the
        ongoing set of entities that must be reestimated at each level of the
        tree.

        Level 0: [SubAccount, Markup]
            Since the SubAccount level of the ancestry tree is recursive, the
            parent of each :obj:`SubAccount` or :obj:`Markup` can either
            be a :obj:`SubAccount` or a :obj:`Account`.

            Parents: [Account, SubAccount]

        ...

        Level n: [Account, Markup]
            Parents: [Budget]

        Level n + 1: [Budget]
            Parents: None
        """
        commit = kwargs.pop('commit', True)
        subaccounts = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.subaccount_cls)
        ])
        # Set of ongoing Account(s) that need to be saved after they are
        # reestimated, either directly or via the children.
        accounts = set([])

        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.account_cls)
        ])
        # Set of ongoing Budget(s) that need to be saved after they are
        # reestimated, either directly or via the children.
        budgets = set([])

        # Set of ongoing Budget(s) that still need to be reestimated after the
        # children are reestimated.
        budgets_filtration = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.budget_cls)
        ])

        # The returned SubAccount(s) will be those only for which a save is
        # warranted after estimation.
        subaccounts, a, b = self.model.subaccount_cls.objects.bulk_estimate(
            instances=subaccounts,
            commit=False,
            **kwargs
        )
        # The returned Budget(s) will be estimated, and thus require a save.
        # So we need to remove them from the filtration so as to not estimate
        # them again and add them to the set of Budget(s) to save at the end.
        budgets.update(b)
        budgets_filtration = budgets_filtration.difference(b)

        # The returned Account(s) will be estimated, and thus require a save.
        # So we need to remove them from the filtration so as to not estimate
        # them again and add them to the set of Account(s) to save at the end.
        accounts.update(a)
        accounts_filtration = accounts_filtration.difference(a)

        # Since we are saving all of the instances at the end, we need to
        # to provide the unsaved children to the actualization so that their
        # updated values are included in any potential calculations.
        unsaved_account_children = {}
        for obj in subaccounts:
            unsaved_account_children.setdefault(obj.parent.pk, [])
            unsaved_account_children[obj.parent.pk].append(obj)

        # The returned Account(s) will be those only for which a save is
        # warranted after estimation.
        a, b = self.model.account_cls.objects.bulk_estimate(
            instances=accounts_filtration,
            commit=False,
            unsaved_children=unsaved_account_children,
            **kwargs
        )
        accounts.update(a)

        # The returned Budget(s) will be estimated, and thus require a save.
        # So we need to remove them from the filtration so as to not estimate
        # them again and add them to the set of Budget(s) to save at the end.
        budgets_filtration = budgets_filtration.difference(b)
        budgets.update(b)

        # Since we are saving all of the instances at the end, we need to
        # to provide the unsaved children to the actualization so that their
        # updated values are included in any potential calculations.
        unsaved_budget_children = {}
        for obj in accounts:
            unsaved_budget_children.setdefault(obj.parent.pk, [])
            unsaved_budget_children[obj.parent.pk].append(obj)

        # The returned Budget(s) will be those only for which a save is
        # warranted after estimation.
        b = self.model.budget_cls.objects.bulk_estimate(
            instances=budgets_filtration,
            commit=False,
            unsaved_children=unsaved_budget_children,
            **kwargs
        )
        budgets.update(b)

        if commit:
            self.model.subaccount_cls.objects.bulk_update_post_estimation(
                instances=subaccounts
            )
            self.model.account_cls.objects.bulk_update_post_estimation(
                instances=accounts
            )
            self.model.budget_cls.objects.bulk_update_post_estimation(
                instances=budgets
            )
        return subaccounts, accounts, budgets

    @signals.disable()
    def bulk_actualize_all(self, instances, **kwargs):
        """
        Performs the actualization routines on the provided instances, which
        can consist of instances of :obj:`BudgetAccount`, :obj:`Budget`,
        :obj:`Markup` and :obj:`BudgetSubAccount`.

        The actualization methodology behaves like a filtration, starting
        at the lowest point of the budget ancestry tree and working it's
        way upwards, keeping track of every entity that needs to be
        reactualized (i.e. it's actual value is recalculated) as a result of
        the actual value of one of it's children changing.

        Consider the definition of the budget ancestry tree to be the tree
        that is constructed from the parent/child relationships amongst the
        entities of a :obj:`Budget` or :obj:`Template`:

        - Budget
            - BudgetAccount
                - BudgetSubAccount
                    - BudgetSubAccount
                    - Markup
                - BudgetSubAccount
                - BudgetSubAccount
                - Markup
                - Markup
            - BudgetAccount
                - BudgetSubAccount
                    - BudgetSubAccount
                    - BudgetSubAccount
                - Markup
            - BudgetAccount
            - Markup

        The filtration starts at the lowest level of the tree, which consists
        of :obj:`SubAccount`(s) and :obj:`Markup`(s).  Each entity in the lowest
        level of the tree is reactualized.  If it is determined that the actual
        value changed, then we must also reactualize it's parent.  So the parent
        is added to the ongoing set of entities that must be reactualized at
        each level of the tree.

        Level 0: [BudgetSubAccount, Markup]
            Since the SubAccount level of the ancestry tree is recursive, the
            parent of each :obj:`BudgetSubAccount` or :obj:`Markup` can either
            be a :obj:`BudgetSubAccount` or a :obj:`BudgetAccount`.

            Parents: [BudgetAccount, BudgetSubAccount]

        ...

        Level n: [BudgetAccount, Markup]
            Parents: [Budget]

        Level n + 1: [Budget]
            Parents: None
        """
        from greenbudget.app.account.models import BudgetAccount
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.markup.models import Markup
        from greenbudget.app.subaccount.models import BudgetSubAccount

        commit = kwargs.pop('commit', True)
        markups = set([
            obj for obj in instances if isinstance(obj, Markup)])
        # If an Actual is associated with a Markup instance, the parent of that
        # Markup instance must be reactualized - we do not have to reactualize
        # the Markup itself because it's actual value is derived from an
        # @property.
        subaccounts = set([
            obj for obj in ensure_iterable(instances)
            + [m.parent for m in markups]
            if isinstance(obj, BudgetSubAccount)
        ])
        # Set of ongoing Account(s) that need to be saved after they are
        # reactualized, either directly or via the children.
        accounts = set([])

        # Set of ongoing Budget(s) that need to be saved after they are
        # reactualized, either directly or via the children.
        budgets = set([])

        # Set of ongoing budgets that still need to be reactualized after the
        # children are reactualized.
        budgets_filtration = set([
            obj for obj in ensure_iterable(instances)
            + [m.parent for m in markups]
            if isinstance(obj, Budget)
        ])
        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in ensure_iterable(instances)
            + [m.parent for m in markups]
            if isinstance(obj, BudgetAccount)
        ])
        # The returned SubAccount(s) will be those only for which a save is
        # warranted after actualization.
        subaccounts, a, b = BudgetSubAccount.objects.bulk_actualize(
            instances=subaccounts,
            commit=False,
            **kwargs
        )
        # The returned Budget(s) will be actualized, and thus require a save.
        # So we need to remove them from the filtration so as to not actualize
        # them again and add them to the set of Budget(s) to save at the end.
        budgets.update(b)
        budgets_filtration = budgets_filtration.difference(b)

        # The returned Account(s) will be actualized, and thus require a save.
        # So we need to remove them from the filtration so as to not actualize
        # them again and add them to the set of Account(s) to save at the end.
        accounts.update(a)
        accounts_filtration = accounts_filtration.difference(a)

        # Since we are saving all of the instances at the end, we need to
        # to provide the unsaved children to the actualization so that their
        # updated values are included in any potential calculations.
        unsaved_account_children = {}
        for obj in subaccounts:
            unsaved_account_children.setdefault(obj.parent.pk, [])
            unsaved_account_children[obj.parent.pk].append(obj)

        # The returned Account(s) will be those only for which a save is
        # warranted after actualization.
        a, b = BudgetAccount.objects.bulk_actualize(
            instances=accounts_filtration,
            commit=False,
            unsaved_children=unsaved_account_children,
            **kwargs
        )
        accounts.update(a)

        # The returned Budget(s) will be estimated, and thus require a save.
        # So we need to remove them from the filtration so as to not estimate
        # them again and add them to the set of Budget(s) to save at the end.
        budgets_filtration = budgets_filtration.difference(b)
        budgets.update(b)

        # Since we are saving all of the instances at the end, we need to
        # to provide the unsaved children to the actualization so that their
        # updated values are included in any potential calculations.
        unsaved_budget_children = {}
        for obj in accounts:
            unsaved_budget_children.setdefault(obj.parent.pk, [])
            unsaved_budget_children[obj.parent.pk].append(obj)

        # The returned Budget(s) will be those only for which a save is
        # warranted after actualization.
        b = Budget.objects.bulk_actualize(
            instances=budgets_filtration,
            commit=False,
            unsaved_children=unsaved_budget_children,
            **kwargs
        )
        budgets.update(b)
        if commit:
            BudgetSubAccount.objects.bulk_update_post_actualization(
                instances=subaccounts
            )
            BudgetAccount.objects.bulk_update_post_actualization(
                instances=accounts
            )
            Budget.objects.bulk_update_post_actualization(
                instances=budgets
            )

        return subaccounts, accounts, budgets

    @signals.disable()
    def bulk_calculate_all(self, instances, **kwargs):
        """
        Performs both the estimation and actualization (if applicable) routines
        on the provided instances, which can consist of instances of
        :obj:`Account`, :obj:`BaseBudget`, :obj:`Markup` and :obj:`SubAccount`.

        The methodology behaves like a filtration, starting at the lowest point
        of the budget ancestry tree and working it's way upwards, keeping track
        of every entity that changed in a way that warrant recalculation of
        it's parent along the way.

        See the documentation for `bulk_estimate_all` and `bulk_actualize_all`
        for more details.
        """
        commit = kwargs.pop('commit', True)
        subaccounts = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.subaccount_cls)
        ])
        # Set of ongoing Account(s) that need to be saved after they are
        # reactualized, either directly or via the children.
        accounts = set([])

        # Set of ongoing Budget(s) that need to be saved after they are
        # reactualized, either directly or via the children.
        budgets = set([])

        # Set of ongoing budgets that still need to be reactualized after the
        # children are reactualized.
        budgets_filtration = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.budget_cls)
        ])

        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in ensure_iterable(instances)
            if isinstance(obj, self.model.account_cls)
        ])
        # The returned SubAccount(s) will be those only for which a save is
        # warranted after actualization.
        subaccounts, a, b = self.model.subaccount_cls.objects.bulk_calculate(
            instances=subaccounts,
            commit=False,
            **kwargs
        )
        # The returned Budget(s) will be calculated, and thus require a save.
        # So we need to remove them from the filtration so as to not calculate
        # them again and add them to the set of Budget(s) to save at the end.
        budgets.update(b)
        budgets_filtration = budgets_filtration.difference(b)

        # The returned Account(s) will be calculated, and thus require a save.
        # So we need to remove them from the filtration so as to not calculate
        # them again and add them to the set of Budget(s) to save at the end.
        accounts.update(a)
        accounts_filtration = accounts_filtration.difference(a)

        # Since we are saving all of the instances at the end, we need to
        # to provide the unsaved children to the actualization so that their
        # updated values are included in any potential calculations.
        unsaved_account_children = {}
        for obj in subaccounts:
            unsaved_account_children.setdefault(obj.parent.pk, [])
            unsaved_account_children[obj.parent.pk].append(obj)

        # The returned Account(s) will be those only for which a save is
        # warranted after recalculation.
        a, b = self.model.account_cls.objects.bulk_calculate(
            instances=accounts_filtration,
            unsaved_children=unsaved_account_children,
            commit=False,
            **kwargs
        )
        accounts.update(a)

        # The returned Budget(s) will be calculated, and thus require a save.
        # So we need to remove them from the filtration so as to not calculate
        # them again and add them to the set of Budget(s) to save at the end.
        budgets_filtration = budgets_filtration.difference(b)
        budgets.update(b)

        # Since we are saving all of the instances at the end, we need to
        # to provide the unsaved children to the actualization so that their
        # updated values are included in any potential calculations.
        unsaved_budget_children = {}
        for obj in accounts:
            unsaved_budget_children.setdefault(obj.parent.pk, [])
            unsaved_budget_children[obj.parent.pk].append(obj)

        # The returned Budget(s) will be those only for which a save is
        # warranted after recalculation.
        b = self.model.budget_cls.objects.bulk_calculate(
            instances=budgets_filtration,
            unsaved_children=unsaved_budget_children,
            commit=False,
            **kwargs
        )
        budgets.update(b)

        if commit:
            self.model.subaccount_cls.objects.bulk_update_post_calculation(
                instances=subaccounts
            )
            self.model.account_cls.objects.bulk_update_post_calculation(
                instances=accounts
            )
            self.model.budget_cls.objects.bulk_update_post_calculation(
                instances=budgets
            )

        return subaccounts, accounts, budgets


class BudgetingRowManagerMixin(RowManagerMixin, BudgetingManagerMixin):
    pass


class BudgetingManager(BudgetingManagerMixin, models.Manager):
    queryset_class = PrePKBulkCreateQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetingRowManager(BudgetingRowManagerMixin, models.Manager):
    queryset_class = RowQuerySet


class BudgetingPolymorphicManager(BudgetingManagerMixin, PolymorphicManager):
    queryset_class = BulkCreatePolymorphicQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetingPolymorphicRowManager(
        BudgetingRowManagerMixin, PolymorphicManager):
    queryset_class = RowPolymorphicQuerySet

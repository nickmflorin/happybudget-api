import logging

from django.db import models
from polymorphic.models import PolymorphicManager

from greenbudget.lib.utils import set_or_list
from greenbudget.app import signals
from .query import (
    BudgetingPolymorphicQuerySet,
    BudgetingQuerySet
)

logger = logging.getLogger('greenbudget')


class BudgetingManagerMixin:
    def bulk_update(self, instances, fields):
        results = super().bulk_update(instances, fields)
        self.cleanup(instances)
        return results

    def bulk_create(self, instances, **kwargs):
        results = super().bulk_create(instances, **kwargs)
        self.cleanup(instances)
        return results

    def cleanup(self, instances, **kwargs):
        for instance in instances:
            # Not all of the models that use these managers will have the
            # CacheControlMixin.
            if hasattr(instance, 'CACHES'):
                instance.invalidate_caches(["detail"])
                if hasattr(instance, 'parent'):
                    instance.parent.invalidate_caches(["detail", "children"])

    def bulk_update_post_calculation(self, instances):
        if instances:
            return self.bulk_update(
                instances=instances,
                fields=self.model.CALCULATED_FIELDS
            )
        return None

    def bulk_update_post_estimation(self, instances):
        if instances:
            return self.bulk_update(
                instances=instances,
                fields=self.model.ESTIMATED_FIELDS
            )
        return None

    def bulk_update_post_actualization(self, instances):
        if instances:
            return self.bulk_update(instances=instances, fields=['actual'])
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

    def validate_instances_before_save(self, instances):
        for instance in instances:
            if hasattr(instance, 'validate_before_save'):
                instance.validate_before_save()

    @signals.disable()
    def bulk_estimate_all(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        subaccounts = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.model.subaccount_cls())
        ])
        # Set of ongoing Account(s) that need to be saved after they are
        # reestimated, either directly or via the children.
        accounts = set([])
        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.model.account_cls())
        ])
        # Set of ongoing Budget(s) that need to be saved after they are
        # reestimated, either directly or via the children.
        budgets = set([])
        # Set of ongoing Budget(s) that still need to be reestimated after the
        # children are reestimated.
        budgets_filtration = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.model.budget_cls())
        ])
        # The returned SubAccount(s) will be those only for which a save is
        # warranted after estimation.
        subaccounts, a, b = self.model.subaccount_cls().objects.bulk_estimate(
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
        a, b = self.model.account_cls().objects.bulk_estimate(
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
        b = self.model.budget_cls().objects.bulk_estimate(
            instances=budgets_filtration,
            commit=False,
            unsaved_children=unsaved_budget_children,
            **kwargs
        )
        budgets.update(b)

        if commit:
            self.model.subaccount_cls().objects.bulk_update_post_estimation(
                instances=subaccounts
            )
            self.model.account_cls().objects.bulk_update_post_estimation(
                instances=accounts
            )
            self.model.budget_cls().objects.bulk_update_post_estimation(
                instances=budgets
            )
        return subaccounts, accounts, budgets

    @signals.disable()
    def bulk_actualize_all(self, instances, **kwargs):
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
            obj for obj in set_or_list(instances) + [m.parent for m in markups]
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
            obj for obj in set_or_list(instances) + [m.parent for m in markups]
            if isinstance(obj, Budget)
        ])
        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in set_or_list(instances) + [m.parent for m in markups]
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
        commit = kwargs.pop('commit', True)
        subaccounts = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.model.subaccount_cls())
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
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.model.budget_cls())
        ])
        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.model.account_cls())
        ])
        # The returned SubAccount(s) will be those only for which a save is
        # warranted after actualization.
        subaccounts, a, b = self.model.subaccount_cls().objects.bulk_calculate(
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
        # warranted after actualization.
        a, b = self.model.account_cls().objects.bulk_calculate(
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
        # warranted after actualization.
        b = self.model.budget_cls().objects.bulk_calculate(
            instances=budgets_filtration,
            unsaved_children=unsaved_budget_children,
            commit=False,
            **kwargs
        )
        budgets.update(b)

        if commit:
            self.model.subaccount_cls().objects.bulk_update_post_calculation(
                instances=subaccounts
            )
            self.model.account_cls().objects.bulk_update_post_calculation(
                instances=accounts
            )
            self.model.budget_cls().objects.bulk_update_post_calculation(
                instances=budgets
            )

        return subaccounts, accounts, budgets


class BudgetingManager(BudgetingManagerMixin, models.Manager):
    queryset_class = BudgetingQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetingPolymorphicManager(BudgetingManagerMixin, PolymorphicManager):
    queryset_class = BudgetingPolymorphicQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model)

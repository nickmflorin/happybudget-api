import logging
from django.db.models import Case, Q, When, Value as V, BooleanField

from greenbudget.lib.utils import set_or_list, humanize_list

from greenbudget.app import signals
from .utils import get_instance_cls


logger = logging.getLogger('greenbudget')


class BaseBudgetQuerier:
    @property
    def base_cls(self):
        from greenbudget.app.budget.models import BaseBudget
        return BaseBudget

    @property
    def budget_cls(self):
        from greenbudget.app.budget.models import Budget
        return Budget

    @property
    def template_cls(self):
        from greenbudget.app.template.models import Template
        return Template

    @property
    def account_cls(self):
        from greenbudget.app.account.models import Account
        return Account

    @property
    def budget_account_cls(self):
        from greenbudget.app.account.models import BudgetAccount
        return BudgetAccount

    @property
    def template_account_cls(self):
        from greenbudget.app.account.models import TemplateAccount
        return TemplateAccount

    @property
    def subaccount_cls(self):
        from greenbudget.app.subaccount.models import SubAccount
        return SubAccount

    @property
    def budget_subaccount_cls(self):
        from greenbudget.app.subaccount.models import BudgetSubAccount
        return BudgetSubAccount

    @property
    def template_subaccount_cls(self):
        from greenbudget.app.subaccount.models import TemplateSubAccount
        return TemplateSubAccount

    @property
    def markup_cls(self):
        from greenbudget.app.markup.models import Markup
        return Markup

    @property
    def group_cls(self):
        from greenbudget.app.group.models import Group
        return Group

    def bulk_update(self, instances, fields, invalidate_caches=True):
        if invalidate_caches:
            for instance in instances:
                # Not all of the models that use these managers will have the
                # CacheControlMixin.
                if hasattr(instance, 'CACHES'):
                    instance.invalidate_detail_cache()
                if hasattr(instance, 'parent'):
                    instance.parent.invalidate_children_cache()
        return super().bulk_update(instances, fields)

    def bulk_update_post_calculation(self, instances, invalidate_caches=True):
        if instances:
            return self.bulk_update(
                instances=instances,
                fields=self.model.CALCULATED_FIELDS,
                invalidate_caches=invalidate_caches
            )
        return None

    def bulk_update_post_estimation(self, instances, invalidate_caches=True):
        if instances:
            return self.bulk_update(
                instances=instances,
                fields=self.model.ESTIMATED_FIELDS,
                invalidate_caches=invalidate_caches
            )
        return None

    def bulk_update_post_actualization(self, instances, invalidate_caches=True):
        if instances:
            return self.bulk_update(
                instances=instances,
                fields=['actual'],
                invalidate_caches=invalidate_caches
            )
        return None

    @signals.disable()
    def bulk_delete_empty_groups(self, groups):
        for group in groups:
            id = group if not isinstance(group, self.group_cls) else group.pk
            if self.model.objects.filter(group_id=id).count() == 0:
                try:
                    self.group_cls.objects.get(pk=id).delete()
                    logger.info(
                        "Deleting group %s after it was removed from %s "
                        "because the group no longer has any children."
                        % (
                            id,
                            self.model.__class__.__name__,
                        )
                    )
                except self.group_cls.DoesNotExist:
                    # We have to be concerned with race conditions here.
                    pass

    def validate_instances_before_save(self, instances):
        for instance in instances:
            if hasattr(instance, 'validate_before_save'):
                instance.validate_before_save()

    def _validate_instances(self, instances, types, func):
        invalid_types = [
            type(i) for i in instances if not isinstance(i, tuple(types))]
        if invalid_types:
            raise Exception(
                "Can only perform action `{func}` on instances of types "
                "{valid}.  Found invalid types {invalid}.".format(
                    func=func.__name__,
                    valid=humanize_list(types),
                    invalid=humanize_list(invalid_types)
                )
            )

    @signals.disable()
    def bulk_estimate_all(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)
        self._validate_instances(
            instances=instances,
            types=[self.base_cls, self.account_cls, self.subaccount_cls],
            func=self.bulk_estimate_all
        )
        subaccounts = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.subaccount_cls)
        ])
        # Set of ongoing Account(s) that need to be saved after they are
        # reestimated, either directly or via the children.
        accounts = set([])
        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.account_cls)
        ])
        # Set of ongoing Budget(s) that need to be saved after they are
        # reestimated, either directly or via the children.
        budgets = set([])
        # Set of ongoing Budget(s) that still need to be reestimated after the
        # children are reestimated.
        budgets_filtration = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.base_cls)
        ])
        # The returned SubAccount(s) will be those only for which a save is
        # warranted after estimation.
        subaccounts, a, b = self.subaccount_cls.objects.bulk_estimate(
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
        a, b = self.account_cls.objects.bulk_estimate(
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
        b = self.base_cls.objects.bulk_estimate(
            instances=budgets_filtration,
            commit=False,
            unsaved_children=unsaved_budget_children,
            **kwargs
        )
        budgets.update(b)

        if commit:
            self.subaccount_cls.objects.bulk_update_post_estimation(
                instances=subaccounts,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )
            self.account_cls.objects.bulk_update_post_estimation(
                instances=accounts,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )
            self.base_cls.objects.bulk_update_post_estimation(
                instances=budgets,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )
        return subaccounts, accounts, budgets

    @signals.disable()
    def bulk_actualize_all(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)

        self._validate_instances(
            instances=instances,
            types=[
                self.budget_cls,
                self.budget_account_cls,
                self.budget_subaccount_cls,
                self.markup_cls
            ],
            func=self.bulk_estimate_all
        )
        markups = set([
            obj for obj in instances if isinstance(obj, self.markup_cls)])
        # If an Actual is associated with a Markup instance, the parent of that
        # Markup instance must be reactualized - we do not have to reactualize
        # the Markup itself because it's actual value is derived from an
        # @property.
        subaccounts = set([
            obj for obj in set_or_list(instances) + [m.parent for m in markups]
            if isinstance(obj, self.budget_subaccount_cls)
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
            if isinstance(obj, self.budget_cls)
        ])
        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in set_or_list(instances) + [m.parent for m in markups]
            if isinstance(obj, self.budget_account_cls)
        ])
        # The returned SubAccount(s) will be those only for which a save is
        # warranted after actualization.
        subaccounts, a, b = self.budget_subaccount_cls.objects.bulk_actualize(
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
        a, b = self.budget_account_cls.objects.bulk_actualize(
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
        b = self.budget_cls.objects.bulk_actualize(
            instances=budgets_filtration,
            commit=False,
            unsaved_children=unsaved_budget_children,
            **kwargs
        )
        budgets.update(b)
        if commit:
            self.budget_subaccount_cls.objects.bulk_update_post_actualization(
                instances=subaccounts,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )
            self.budget_account_cls.objects.bulk_update_post_actualization(
                instances=accounts,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )
            self.budget_cls.objects.bulk_update_post_actualization(
                instances=budgets,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )

        return subaccounts, accounts, budgets

    @signals.disable()
    def bulk_calculate_all(self, instances, **kwargs):
        commit = kwargs.pop('commit', True)

        self._validate_instances(
            instances=instances,
            types=[
                self.base_cls,
                self.account_cls,
                self.subaccount_cls
            ],
            func=self.bulk_calculate_all
        )
        subaccounts = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.subaccount_cls)
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
            if isinstance(obj, self.base_cls)
        ])
        # Set of ongoing accounts that still need to be reactualized after the
        # children are reactualized.
        accounts_filtration = set([
            obj for obj in set_or_list(instances)
            if isinstance(obj, self.account_cls)
        ])
        # The returned SubAccount(s) will be those only for which a save is
        # warranted after actualization.
        subaccounts, a, b = self.subaccount_cls.objects.bulk_calculate(
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
        a, b = self.account_cls.objects.bulk_calculate(
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
        b = self.base_cls.objects.bulk_calculate(
            instances=budgets_filtration,
            unsaved_children=unsaved_budget_children,
            commit=False,
            **kwargs
        )
        budgets.update(b)

        if commit:
            self.subaccount_cls.objects.bulk_update_post_calculation(
                instances=subaccounts,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )
            self.account_cls.objects.bulk_update_post_calculation(
                instances=accounts,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )
            self.base_cls.objects.bulk_update_post_calculation(
                instances=budgets,
                invalidate_caches=kwargs.get('invalidate_caches', True)
            )

        return subaccounts, accounts, budgets


class TemplateQuerier(BaseBudgetQuerier):
    @property
    def base_cls(self):
        return self.template_cls

    @property
    def account_cls(self):
        return self.template_account_cls

    @property
    def subaccount_cls(self):
        return self.template_subaccount_cls


class BudgetQuerier(BaseBudgetQuerier):
    @property
    def base_cls(self):
        return self.budget_cls

    @property
    def account_cls(self):
        return self.budget_account_cls

    @property
    def subaccount_cls(self):
        return self.budget_subaccount_cls


class BudgetAncestorQuerier:
    def filter_by_budget(self, budget):
        """
        For some models, the model is only tied to a specific :obj:`BaseBudget`
        through it's ancestry trail, not directly.  For instance, in the case
        of the :obj:`group.models.Group`, the ancestry tree might look as
        follows:

        -- Budget
            -- Account
                -- SubAccount
                -- SubAccount
                    -- SubAccount
                    -- SubAccount
                    -- Group (parent = SubAccount)
                -- Group (parent = Account)
            -- Account
                -- SubAccount
                -- SubAccount
                -- Group (parent = Account)
            -- Group (parent = Budget)

        This method allows us to filter the model instances by the specific
        :obj:`BaseBudget` they are associated with at the top of the tree.

        Note:
        ----
        This method is slow, and query intensive, so it should be used
        sparingly.
        """
        return self.annotate(
            _ongoing=Case(
                When(self._get_case_query(budget), then=V(True)),
                default=V(False),
                output_field=BooleanField()
            )
        ).filter(_ongoing=True)

    def _get_case_query(self, budget):
        budget_ct = get_instance_cls(
            obj=budget,
            as_content_type=True,
            obj_type='budget'
        )
        account_ct = get_instance_cls(
            obj=budget,
            as_content_type=True,
            obj_type='account'
        )
        subaccount_ct = get_instance_cls(
            obj=budget,
            as_content_type=True,
            obj_type='subaccount'
        )
        accounts = [
            q[0] for q in account_ct.model_class().objects.filter(parent=budget)
            .only('pk').values_list('pk')
        ]
        subaccounts = [
            q[0] for q in subaccount_ct.model_class().objects
            .filter_by_budget(budget)
            .only('pk').values_list('pk')
        ]
        return (Q(content_type_id=budget_ct) & Q(object_id=budget.pk)) \
            | (Q(content_type_id=account_ct) & Q(object_id__in=accounts)) \
            | (Q(content_type_id=subaccount_ct) & Q(object_id__in=subaccounts))

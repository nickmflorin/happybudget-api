from dataclasses import dataclass, field
import functools
import logging
from typing import Any, List

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.functional import cached_property

from greenbudget.app import signals


logger = logging.getLogger('greenbudget')


@dataclass
class ObjectSet:
    existing: List[Any] = field(default_factory=lambda: [])
    duplicated: List[Any] = field(default_factory=lambda: [])

    @property
    def map(self):
        assert len(self.existing) == len(self.duplicated)
        return {
            self.existing[i].pk: self.duplicated[i].pk
            for i in range(len(self.existing))
        }

    def get_duplicated(self, pk):
        return self.map[pk]

    def add(self, set: Any):
        self.existing += set.existing
        self.duplicated += set.duplicated


def log_after(entity, prefix=None):
    log_prefix = prefix

    def decorator(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            result = func(instance, *args, **kwargs)
            if log_prefix is not None:
                prefix = log_prefix(*args, **kwargs)
                instance.log("%s %sd %s %ss" % (
                    prefix, instance.action_name, len(result.duplicated),
                    entity))
            else:
                instance.log("%sd %s %ss" % (
                    instance.action_name, len(result.duplicated), entity))
            return result
        return inner
    return decorator


class BulkBudgetOperation:
    def __init__(self, budget, user):
        self.original = budget
        self.user = user

    @cached_property
    def budget_model_mapping(self):
        from greenbudget.app.actual.models import Actual
        from greenbudget.app.account.models import BudgetAccount
        from greenbudget.app.fringe.models import Fringe
        from greenbudget.app.group.models import (
            BudgetAccountGroup, BudgetSubAccountGroup)
        from greenbudget.app.subaccount.models import BudgetSubAccount
        return {
            'AccountGroup': BudgetAccountGroup,
            'SubAccountGroup': BudgetSubAccountGroup,
            'SubAccount': BudgetSubAccount,
            'Account': BudgetAccount,
            'Fringe': Fringe,
            'Actual': Actual
        }

    @cached_property
    def template_model_mapping(self):
        from greenbudget.app.account.models import TemplateAccount
        from greenbudget.app.fringe.models import Fringe
        from greenbudget.app.group.models import (
            TemplateAccountGroup, TemplateSubAccountGroup)
        from greenbudget.app.subaccount.models import TemplateSubAccount
        return {
            'AccountGroup': TemplateAccountGroup,
            'SubAccountGroup': TemplateSubAccountGroup,
            'SubAccount': TemplateSubAccount,
            'Account': TemplateAccount,
            'Fringe': Fringe,
        }

    @cached_property
    def model_mapping(self):
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.template.models import Template
        return {
            Budget: self.budget_model_mapping,
            Template: self.template_model_mapping
        }

    def iterate_over_level(self, level=1):
        def iterate_over_subaccounts(obj, current_level):
            for subaccount in obj.subaccounts.all():
                if current_level == level:
                    yield (subaccount, obj)
                else:
                    yield from iterate_over_subaccounts(
                        subaccount, current_level + 1)
        assert level >= 1
        if level == 1:
            for account in self.original.accounts.all():
                yield (account, self.original)
        if level >= 2:
            for account in self.original.accounts.all():
                yield from iterate_over_subaccounts(account, 2)

    def model_cls(self, common_name, base=None):
        base = base or type(self.original)
        return self.model_mapping[base][common_name]

    def instantiate_obj(self, obj, model_cls=None, **overrides):
        kwargs = {}
        for fld in getattr(obj, self.model_fields_arg, []):
            kwargs[fld] = getattr(obj, fld)
        if hasattr(obj.__class__, 'created_by'):
            kwargs['created_by'] = self.user
        if hasattr(obj.__class__, 'updated_by'):
            kwargs['updated_by'] = self.user
        model_cls = model_cls or type(obj)
        return model_cls(**kwargs, **overrides)

    def log(self, message):
        message = "[%s of %s %s] %s" % (
            self.action_name, type(self.budget).__name__, self.budget.pk,
            message)
        logger.info(message)

    def bulk_create(self, model_name, objs, **kwargs):
        return self.model_cls(model_name).objects.bulk_create(objs, **kwargs)

    def objects(self, model_name):
        return self.model_cls(model_name).objects

    @log_after(entity="Fringe")
    def handle_fringes(self):
        from greenbudget.app.fringe.models import Fringe
        # We duplicate all of the associated Fringes at once, and then tie them
        # to the individual SubAccount(s) as they are created.
        fringes_set = ObjectSet(existing=self.original.fringes.all())
        fringes_set.duplicated = Fringe.objects.bulk_create([
            self.instantiate_obj(fringe, budget=self.budget)
            for fringe in fringes_set.existing
        ])
        return fringes_set

    @log_after(entity="Account Group")
    def handle_account_groups(self):
        account_group_set = ObjectSet(
            existing=self.objects('AccountGroup')
            .filter(parent=self.original).all()
        )
        account_group_set.duplicated = self.bulk_create(
            model_name="AccountGroup",
            objs=[
                self.instantiate_obj(group, parent=self.budget)
                for group in account_group_set.existing
            ],
            return_created_objects=True
        )
        return account_group_set

    @log_after(entity="Account")
    def handle_accounts(self):
        account_group_set = self.handle_account_groups()

        account_set = ObjectSet()
        account_set.existing = self.original.accounts.all()
        for account in account_set.existing:
            kwargs = {'budget': self.budget}
            if account.group is not None:
                kwargs['group_id'] = account_group_set.get_duplicated(
                    account.group.pk)
            account_set.duplicated.append(self.instantiate_obj(
                account, **kwargs))

        account_set.duplicated = self.bulk_create(
            model_name='Account',
            objs=account_set.duplicated,
            return_created_objects=True
        )
        return account_set

    @log_after(
        entity="Sub Account Group",
        prefix=lambda level, parent_set: "Level %s:" % level
    )
    def handle_subaccount_groups(self, level, parent_set):
        # For any given level of the budget tree, we first need to look at
        # the groups associated with that level and duplicate them,
        # maintaining a map of the original group to the duplicated group.
        #
        # For any given level N of the tree, the items in level N are
        # associated with Group(s) that have the object at level N - 1 as
        # the parent.
        #
        # This can be seen in this tree diagram:
        #
        # Budget (Level 0)
        # -- Groups: [Group(parent=Budget), Group(parent=Budget)] = [A, B]
        # -- Accounts
        # ---- Account 1 => Group A
        # ------ Groups: [Group(parent=Account 1), Group(parent=Account 1)] = [C, D]  # noqa
        # ------ SubAccounts
        # -------- SubAccount 1 => Group C
        # -------- SubAccount 2 => Group C
        # ---- Account 2 => Group B
        group_set = ObjectSet()
        for parent, _ in self.iterate_over_level(level=level - 1):
            parent_subaccount_groups = self.objects('SubAccountGroup').filter(
                object_id=parent.pk,
                content_type=ContentType.objects.get_for_model(type(parent))
            ).all()
            group_set.existing += parent_subaccount_groups
            parent_cls = self.subaccount_parent_cls(parent)
            group_set.duplicated += [
                self.instantiate_obj(
                    obj=group,
                    parent=parent_cls.objects.get(pk=parent_set.map[parent.pk])
                )
                for group in parent_subaccount_groups
            ]
        if len(group_set.duplicated) != 0:
            group_set.duplicated = self.bulk_create(
                model_name='SubAccountGroup',
                objs=group_set.duplicated,
                return_created_objects=True
            )
        return group_set

    def assign_fringes_to_subaccounts(self, subaccount_set, fringes_set):
        # Unfortunately, we cannot set M2M fields during a bulk create,
        # so we must handle fringes after the duplication.
        self.log("Assigning Fringes for Sub Accounts.")
        for obj in subaccount_set.existing:
            if obj.fringes.count() != 0:
                duplicated = subaccount_set.get_duplicated(obj.pk)
                duplicated.fringes.set([
                    fringes_set.get_duplicated(old_fringe.pk)
                    for old_fringe in obj.fringes.all()
                ])

    @log_after(
        entity="Sub Account",
        prefix=lambda level, parent_set: "Level %s:" % level
    )
    def handle_subaccounts_at_level(self, level, parent_set):
        group_set = self.handle_subaccount_groups(level, parent_set)
        # Now that we have duplicated the Groups that are used for this level,
        # we can duplicate the actual objects at this level, maintaining a map
        # of the existing object to the duplicated object.
        subaccount_set = ObjectSet()
        for obj, parent in self.iterate_over_level(level=level):
            subaccount_set.existing.append(obj)
            kwargs = {'budget': self.budget}
            if obj.group is not None:
                assert len(group_set.duplicated) != 0
                kwargs['group_id'] = group_set.map[obj.group.pk]

            # Assign the duplicated object the duplicated parent that is
            # associated with the original parent (duplicated in previous
            # level).
            parent_cls = self.subaccount_parent_cls(parent)
            kwargs['parent'] = parent_cls.objects.get(pk=parent_set.map[parent.pk])  # noqa

            duplicated_obj = self.instantiate_obj(obj, **kwargs)

            # This is currently handled by a post_save signal in
            # greenbudget.app.subaccount.signals - but since we are disabling
            # signals for performance, we have to do it the faster way here.
            if obj.subaccounts.count() != 0:
                for fld in duplicated_obj.DERIVING_FIELDS:
                    setattr(duplicated_obj, fld, None)

            subaccount_set.duplicated.append(duplicated_obj)

        if len(subaccount_set.duplicated) != 0:
            subaccount_set.duplicated = self.bulk_create(
                model_name='SubAccount',
                objs=subaccount_set.duplicated,
                return_created_objects=True
            )
        return subaccount_set

    @log_after(entity="Overall Sub Account")
    def handle_subaccounts(self, account_set):
        # Set to hold all cumulatively duplicated SubAccount(s), at any level.
        subaccount_set = ObjectSet()

        def handle_subaccount_level(parent_set, level=2):
            self.log("Level %s: Duplicating Sub Accounts" % level)
            level_set = self.handle_subaccounts_at_level(level, parent_set)
            subaccount_set.add(level_set)
            if len(level_set.duplicated) != 0:
                handle_subaccount_level(
                    level=level + 1,
                    parent_set=level_set
                )
        handle_subaccount_level(parent_set=account_set)
        return subaccount_set


class BudgetDeriver(BulkBudgetOperation):
    model_fields_arg = 'FIELDS_TO_DERIVE'
    action_name = 'Derive'

    @transaction.atomic
    @signals.disable([
        signals.post_save,
        signals.post_create_by_user,
        signals.post_create,
        signals.fields_changed,
        signals.field_changed
    ])
    def derive(self, **kwargs):
        from greenbudget.app.budget.models import Budget

        self.budget = self.instantiate_obj(self.original, model_cls=Budget)
        for k, v in kwargs.items():
            setattr(self.budget, k, v)

        self.budget.save()
        logger.info("Derived %s %s -> %s." % (
            type(self.budget).__name__, self.original.pk, self.budget.pk))

        fringes_set = self.handle_fringes()
        account_set = self.handle_accounts()
        subaccount_set = self.handle_subaccounts(account_set)
        self.assign_fringes_to_subaccounts(subaccount_set, fringes_set)

        return self.budget

    def get_budget_form(self, obj):
        for k, v in self.template_model_mapping.items():
            if type(obj) is v:
                return self.budget_model_mapping[k]
        return None

    def instantiate_obj(self, obj, model_cls=None, **overrides):
        model_cls = model_cls or self.get_budget_form(obj)
        return super().instantiate_obj(obj, model_cls=model_cls, **overrides)

    def bulk_create(self, model_name, objs, **kwargs):
        model_cls = self.budget_model_mapping[model_name]
        return model_cls.objects.bulk_create(objs, **kwargs)

    def objects(self, model_name):
        model_cls = self.template_model_mapping[model_name]
        return model_cls.objects

    def subaccount_parent_cls(self, parent):
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.template.models import Template
        if type(parent) is self.model_cls('Account', base=Template):
            return self.model_cls('Account', base=Budget)
        assert type(parent) is self.model_cls('SubAccount', base=Template)
        return self.model_cls('SubAccount', base=Budget)


class BudgetDuplicator(BulkBudgetOperation):
    model_fields_arg = 'FIELDS_TO_DUPLICATE'
    action_name = 'Duplicate'

    @transaction.atomic
    @signals.disable([
        signals.post_save,
        signals.post_create_by_user,
        signals.post_create,
        signals.fields_changed,
        signals.field_changed
    ])
    def duplicate(self):
        from greenbudget.app.template.models import Template

        self.budget = self.instantiate_obj(self.original)
        self.budget.save()
        logger.info("Duplicated %s %s -> %s." % (
            type(self.budget).__name__, self.original.pk, self.budget.pk))

        fringes_set = self.handle_fringes()
        account_set = self.handle_accounts()
        subaccount_set = self.handle_subaccounts(account_set)
        self.assign_fringes_to_subaccounts(subaccount_set, fringes_set)

        if not isinstance(self.budget, Template):
            # We need to wait until all of the SubAccount(s) are created before
            # we can bulk create the actuals.
            self.handle_actuals(subaccount_set)
        return self.budget

    def subaccount_parent_cls(self, parent):
        return type(parent)

    def handle_actuals(self, subaccount_set):
        from greenbudget.app.actual.models import Actual
        duplicated_actuals = []
        for actual in Actual.objects.filter(budget=self.original).all():
            kwargs = {'budget': self.budget}
            if actual.subaccount is not None:
                kwargs['subaccount_id'] = subaccount_set.map[actual.subaccount.pk]  # noqa
            duplicated_actuals.append(self.instantiate_obj(actual, **kwargs))

        Actual.objects.bulk_create(duplicated_actuals)
        self.log("Duplicated %s Actuals" % len(duplicated_actuals))

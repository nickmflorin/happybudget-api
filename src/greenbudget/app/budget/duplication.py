from dataclasses import dataclass, field
import functools
import logging
from typing import Any, List

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from greenbudget.app import signals
from greenbudget.app.budgeting.utils import get_instance_cls


logger = logging.getLogger('greenbudget')


@dataclass
class ObjectSet:
    existing: List[Any] = field(default_factory=lambda: [])
    duplicated: List[Any] = field(default_factory=lambda: [])

    @property
    def map(self):
        assert len(self.existing) == len(self.duplicated)
        if any([dup.pk is None for dup in self.duplicated]):
            raise Exception(
                "The primary key values must be attributed to the duplicated "
                "set before we can map the existing object to the duplicated "
                "one."
            )
        return {
            self.existing[i].pk: self.duplicated[i]
            for i in range(len(self.existing))
        }

    def get_duplicated(self, pk):
        return self.map[pk]

    def add(self, obj_set: Any):
        self.existing += obj_set.existing
        self.duplicated += obj_set.duplicated


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

    def iterate_over_level(self, level=1):
        def iterate_over_subaccounts(obj, current_level):
            for subaccount in obj.children.all():
                if current_level == level:
                    yield (subaccount, obj)
                else:
                    yield from iterate_over_subaccounts(
                        subaccount, current_level + 1)
        assert level >= 1
        if level == 1:
            for account in self.original.children.all():
                yield (account, self.original)
        if level >= 2:
            for account in self.original.children.all():
                yield from iterate_over_subaccounts(account, 2)

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

    def bulk_create_non_polymorphic_set(self, model_cls, model_set):
        # For non-polymorphic models, we cannot leverage our custom
        # Polymorphic Bulk Create manager which will return the created IDs.
        # Note: This workaround is query intensive, and if there is a way to
        # speed it up, we should do that.
        original_ids = [
            obj[0]
            for obj in list(model_cls.objects.only('pk').values_list('pk'))
        ]
        model_cls.objects.bulk_create(model_set.duplicated)
        model_set.duplicated = model_cls.objects.exclude(
            pk__in=original_ids).order_by('pk')
        assert len(model_set.duplicated) == len(model_set.existing)
        return model_set

    @log_after(entity="Fringe")
    def handle_fringes(self):
        from greenbudget.app.fringe.models import Fringe
        # We duplicate all of the associated Fringes at once, and then tie them
        # to the individual SubAccount(s) as they are created.
        fringes_set = ObjectSet(existing=self.original.fringes.all())
        fringes_set.duplicated = [
            self.instantiate_obj(fringe, model_cls=Fringe, budget=self.budget)
            for fringe in fringes_set.existing
        ]
        return self.bulk_create_non_polymorphic_set(Fringe, fringes_set)

    @log_after(entity="Markup")
    def handle_markups(self, account_set, subaccount_set):
        from greenbudget.app.markup.models import Markup
        markup_set = ObjectSet(
            existing=Markup.objects.filter_by_budget(self.original).all())

        instantiated_markups = []
        for markup in markup_set.existing:
            assert markup.parent.type in (
                'budget', 'template', 'account', 'subaccount')
            if markup.parent.type in ('budget', 'template'):
                parent = self.budget
            elif markup.parent.type == 'account':
                parent = account_set.get_duplicated(markup.parent.pk)
            else:
                parent = subaccount_set.get_duplicated(markup.parent.pk)
            instantiated_markups.append(self.instantiate_obj(
                markup,
                model_cls=Markup,
                content_type=ContentType.objects.get_for_model(type(parent)),
                object_id=parent.pk
            ))
        markup_set.duplicated = instantiated_markups
        return self.bulk_create_non_polymorphic_set(Markup, markup_set)

    def create_group_set_for_parent(self, original_parent, new_parent,
            persist=True, already_duplicated_originals=None):
        from greenbudget.app.group.models import Group

        already_duplicated_originals = already_duplicated_originals or []
        account_group_set = ObjectSet(
            existing=Group.objects.filter(
                content_type=ContentType.objects.get_for_model(type(original_parent)),  # noqa
                object_id=self.original.pk
            ).exclude(pk__in=already_duplicated_originals)
        )
        account_group_set.duplicated = [
            self.instantiate_obj(
                obj=group,
                model_cls=Group,
                content_type=ContentType.objects.get_for_model(type(new_parent)),  # noqa
                object_id=new_parent.pk
            )
            for group in account_group_set.existing
        ]
        if persist:
            self.bulk_create_non_polymorphic_set(Group, account_group_set)
        return account_group_set

    @log_after(entity="Account Group")
    def handle_account_groups(self):
        return self.create_group_set_for_parent(self.original, self.budget)

    @log_after(entity="Account")
    def handle_accounts(self):
        from greenbudget.app.account.models import BudgetAccount

        account_group_set = self.handle_account_groups()
        account_set = ObjectSet(existing=self.original.children.all())
        for account in account_set.existing:
            kwargs = {'parent': self.budget}
            if account.group is not None:
                kwargs['group_id'] = account_group_set.get_duplicated(
                    account.group.pk).pk
            account_set.duplicated.append(self.instantiate_obj(
                account,
                model_cls=BudgetAccount,
                **kwargs
            ))

        account_set.duplicated = BudgetAccount.objects.bulk_create(
            account_set.duplicated,
            return_created_objects=True
        )
        return account_set

    @log_after(
        entity="Group",
        prefix=lambda level, parent_set: "Level %s:" % level
    )
    def handle_subaccount_groups(self, level, parent_set):
        from greenbudget.app.group.models import Group
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
            parent_cls = self.subaccount_parent_cls(parent)
            group_set_iteree = self.create_group_set_for_parent(
                original_parent=parent,
                new_parent=parent_cls.objects.get(
                    pk=parent_set.map[parent.pk]),
                persist=False,
                already_duplicated_originals=[
                    obj.pk for obj in group_set.existing]
            )
            group_set.add(group_set_iteree)

        self.bulk_create_non_polymorphic_set(Group, group_set)
        return group_set

    def assign_markups_to_accounts(self, account_set, markups_set):
        # Unfortunately, we cannot set M2M fields during a bulk create,
        # so we must handle markups after the duplication.
        self.log("Assigning Markups for Accounts.")
        for obj in account_set.existing:
            if obj.markups.count() != 0:
                duplicated = account_set.get_duplicated(obj.pk)
                duplicated.markups.set([
                    markups_set.get_duplicated(old_markup.pk)
                    for old_markup in obj.markups.all()
                ])

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
        from greenbudget.app.subaccount.models import BudgetSubAccount

        group_set = self.handle_subaccount_groups(level, parent_set)
        # Now that we have duplicated the Groups that are used for this level,
        # we can duplicate the actual objects at this level, maintaining a map
        # of the existing object to the duplicated object.
        subaccount_set = ObjectSet()
        for obj, parent in self.iterate_over_level(level=level):
            subaccount_set.existing.append(obj)
            kwargs = {}
            if obj.group is not None:
                assert len(group_set.duplicated) != 0
                kwargs['group_id'] = group_set.get_duplicated(obj.group.pk).pk

            # Assign the duplicated object the duplicated parent that is
            # associated with the original parent (duplicated in previous
            # level).
            parent_cls = self.subaccount_parent_cls(parent)
            kwargs.update(
                content_type=ContentType.objects.get_for_model(parent_cls),
                object_id=parent.pk
            )
            kwargs['parent'] = parent_cls.objects.get(pk=parent_set.map[parent.pk])  # noqa

            duplicated_obj = self.instantiate_obj(
                obj,
                model_cls=BudgetSubAccount,
                **kwargs
            )

            # This is currently handled by a post_save signal in
            # greenbudget.app.subaccount.signals - but since we are disabling
            # signals for performance, we have to do it the faster way here.
            if obj.children.count() != 0:
                for fld in duplicated_obj.DERIVING_FIELDS:
                    setattr(duplicated_obj, fld, None)

            subaccount_set.duplicated.append(duplicated_obj)

        if len(subaccount_set.duplicated) != 0:
            subaccount_set.duplicated = BudgetSubAccount.objects.bulk_create(
                subaccount_set.duplicated,
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

    def subaccount_parent_cls(self, parent):
        from greenbudget.app.account.models import BudgetAccount
        from greenbudget.app.subaccount.models import BudgetSubAccount
        if parent.type == "account":
            return BudgetAccount
        assert parent.type == "subaccount"
        return BudgetSubAccount


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
        markup_set = self.handle_markups(account_set, subaccount_set)

        self.assign_markups_to_accounts(account_set, markup_set)
        self.assign_markups_to_accounts(subaccount_set, markup_set)
        self.assign_fringes_to_subaccounts(subaccount_set, fringes_set)

        return self.budget

    def instantiate_obj(self, obj, model_cls=None, **overrides):
        from greenbudget.app.budget.models import Budget
        if model_cls is None:
            model_cls = get_instance_cls(obj=Budget, obj_type=obj.type)
        return super().instantiate_obj(obj, model_cls=model_cls, **overrides)


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
        markup_set = self.handle_markups(account_set, subaccount_set)

        self.assign_markups_to_accounts(account_set, markup_set)
        self.assign_markups_to_accounts(subaccount_set, markup_set)
        self.assign_fringes_to_subaccounts(subaccount_set, fringes_set)

        if not isinstance(self.budget, Template):
            # We need to wait until all of the SubAccount(s) are created before
            # we can bulk create the actuals.
            self.handle_actuals(subaccount_set, markup_set)
        return self.budget

    def handle_actuals(self, subaccount_set, markup_set):
        from greenbudget.app.actual.models import Actual
        from greenbudget.app.markup.models import Markup
        from greenbudget.app.subaccount.models import BudgetSubAccount

        duplicated_actuals = []
        for actual in Actual.objects.filter(budget=self.original) \
                .only('content_type', 'object_id') \
                .all():
            kwargs = {'budget': self.budget}
            if actual.owner is not None:
                assert isinstance(actual.owner, (Markup, BudgetSubAccount))
                if isinstance(actual.owner, BudgetSubAccount):
                    kwargs['object_id'] = subaccount_set.get_duplicated(
                        actual.owner.pk).pk
                else:
                    kwargs['object_id'] = markup_set.get_duplicated(
                        actual.owner.pk).pk
                kwargs['content_type'] = ContentType.objects.get_for_model(
                    type(actual.owner))
            duplicated_actuals.append(self.instantiate_obj(
                actual, model_cls=Actual, **kwargs))

        # We do not have to worry about including the primary keys on the
        # bulk created Actual instances because we do not need to map the
        # original Actual instances to the duplicated ones.
        Actual.objects.bulk_create(duplicated_actuals)
        self.log("Duplicated %s Actuals" % len(duplicated_actuals))

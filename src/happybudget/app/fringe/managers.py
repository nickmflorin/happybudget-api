from django.contrib.contenttypes.models import ContentType

from happybudget.lib.utils import concat, ensure_iterable

from happybudget.app import signals
from happybudget.app.account.cache import (
    account_instance_cache, account_children_cache)
from happybudget.app.budget.cache import (
    budget_fringes_cache, budget_instance_cache)
from happybudget.app.budgeting.managers import BudgetingOrderedRowManager
from happybudget.app.subaccount.cache import (
    subaccount_instance_cache, subaccount_children_cache)
from happybudget.app.tabling.query import (
    OrderedRowQuerier, OrderedRowQuerySet)


class FringeQuerier(OrderedRowQuerier):

    def for_budgets(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.budget.models import Budget
        ctype_id = ContentType.objects.get_for_model(Budget).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)

    def for_templates(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.template.models import Template
        ctype_id = ContentType.objects.get_for_model(Template).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)


class FringeQuerySet(FringeQuerier, OrderedRowQuerySet):
    pass


class FringeManager(FringeQuerier, BudgetingOrderedRowManager):
    queryset_class = FringeQuerySet

    @signals.disable()
    def bulk_estimate_fringe_subaccounts(self, fringes, **kwargs):
        fringes = ensure_iterable(fringes)
        subs = set(concat([
            list(obj.subaccounts.all()) for obj in fringes]))

        # The Budget(s)/Template(s), Account(s) and SubAccount(s) that were
        # reestimated as a result of changes to the Fringe/Fringe(s).
        tree = self.model.subaccount_cls.objects.bulk_estimate(subs, **kwargs)

        budget_instance_cache.invalidate(tree.budgets)

        # We only have to invalidate the Account(s) that have been reestimated
        # because Account(s) do not have a concrete reference to a Fringe.
        account_instance_cache.invalidate(tree.accounts, ignore_deps=True)

        # We have to invalidate the caches for SubAccount(s) regardless of
        # whether or not they were reestimated, because they have concrete
        # references to Fringe(s) in their detail/list responses.
        subaccount_instance_cache.invalidate(subs, ignore_deps=True)
        account_instance_cache.invalidate([
            s.parent for s in subs
            if isinstance(s.parent, self.model.account_cls)
        ])
        account_children_cache.invalidate([
            s.parent for s in subs
            if isinstance(s.parent, self.model.account_cls)
        ])
        subaccount_instance_cache.invalidate([
            s.parent for s in subs
            if isinstance(s.parent, self.model.subaccount_cls)
        ])
        subaccount_children_cache.invalidate([
            s.parent for s in subs
            if isinstance(s.parent, self.model.subaccount_cls)
        ])

    @signals.disable()
    def bulk_delete(self, instances, request=None):
        budgets = set([obj.budget for obj in instances])
        self.bulk_estimate_fringe_subaccounts(
            fringes=instances,
            fringes_to_be_deleted=[f.pk for f in instances]
        )
        for obj in instances:
            obj.delete()

        budget_fringes_cache.invalidate(budgets)
        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(budgets, request.user)

    @signals.disable()
    def bulk_add(self, instances, request=None):
        # In the case that the Fringe is added with a flat value, the cutoff
        # is irrelevant.
        for instance in [
                i for i in instances if i.unit == self.model.UNITS.flat]:
            instance.cutoff = None
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, predetermine_pks=True)
        self.bulk_estimate_fringe_subaccounts(created)

        budget_fringes_cache.invalidate(set([obj.budget for obj in created]))
        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(created, request.user)
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields, request=None):
        # In the case that the Fringe is added with a flat value, the cutoff
        # is irrelevant.
        for instance in [
                i for i in instances if i.unit == self.model.UNITS.flat]:
            instance.cutoff = None

        updated = self.bulk_update(instances, update_fields)
        self.bulk_estimate_fringe_subaccounts(instances)

        budget_fringes_cache.invalidate(set([obj.budget for obj in instances]))
        # If the bulk operation is not being performed inside the context of
        # an active request, we should not mark the Budget(s) as having been
        # updated because the method is being called programatically.
        if request is not None:
            self.mark_budgets_updated(instances, request.user)
        return updated


class BudgetFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_budgets()


class TemplateFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_templates()

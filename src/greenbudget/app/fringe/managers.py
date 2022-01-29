from django.contrib.contenttypes.models import ContentType

from greenbudget.lib.utils import concat, ensure_iterable

from greenbudget.app import signals
from greenbudget.app.account.cache import (
    account_instance_cache, account_subaccounts_cache)
from greenbudget.app.budget.cache import (
    budget_fringes_cache, budget_instance_cache)
from greenbudget.app.budgeting.managers import BudgetingRowManager
from greenbudget.app.subaccount.cache import (
    subaccount_instance_cache, subaccount_subaccounts_cache)
from greenbudget.app.tabling.query import RowQuerier, RowQuerySet


class FringeQuerier(RowQuerier):

    def for_budgets(self):
        ctype_id = ContentType.objects.get_for_model(self.model.budget_cls).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)

    def for_templates(self):
        ctype_id = ContentType.objects.get_for_model(
            self.model.template_cls()).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)


class FringeQuerySet(FringeQuerier, RowQuerySet):
    pass


class FringeManager(FringeQuerier, BudgetingRowManager):
    queryset_class = FringeQuerySet

    @signals.disable()
    def bulk_estimate_fringe_subaccounts(self, fringes, **kwargs):
        from greenbudget.app.account.models import Account
        from greenbudget.app.subaccount.models import SubAccount

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
            s.parent for s in subs if isinstance(s.parent, Account)
        ])
        account_subaccounts_cache.invalidate([
            s.parent for s in subs if isinstance(s.parent, Account)
        ])
        subaccount_instance_cache.invalidate([
            s.parent for s in subs if isinstance(s.parent, SubAccount)
        ])
        subaccount_subaccounts_cache.invalidate([
            s.parent for s in subs if isinstance(s.parent, SubAccount)
        ])

    @signals.disable(test=True)
    def bulk_delete(self, instances):
        budgets = set([obj.budget for obj in instances])
        self.bulk_estimate_fringe_subaccounts(
            fringes=instances,
            fringes_to_be_deleted=[f.pk for f in instances]
        )
        for obj in instances:
            obj.delete()

        budget_fringes_cache.invalidate(budgets)
        self.mark_budgets_updated(budgets)

    @signals.disable()
    def bulk_add(self, instances):
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
        self.mark_budgets_updated(created)
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        # In the case that the Fringe is added with a flat value, the cutoff
        # is irrelevant.
        for instance in [
                i for i in instances if i.unit == self.model.UNITS.flat]:
            instance.cutoff = None

        updated = self.bulk_update(instances, update_fields)
        self.bulk_estimate_fringe_subaccounts(instances)

        budget_fringes_cache.invalidate(set([obj.budget for obj in instances]))

        self.mark_budgets_updated(instances)
        return updated


class BudgetFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_budgets()


class TemplateFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_templates()

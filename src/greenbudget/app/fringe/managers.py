from django.contrib.contenttypes.models import ContentType

from greenbudget.lib.utils import concat

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_fringes_cache
from greenbudget.app.budgeting.managers import BudgetingManager
from greenbudget.app.budgeting.query import BudgetingQuerySet


class FringeQuerier:

    def for_budgets(self):
        # pylint: disable=no-member
        ctype_id = ContentType.objects.get_for_model(self.model.budget_cls()).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)

    def for_templates(self):
        # pylint: disable=no-member
        ctype_id = ContentType.objects.get_for_model(
            self.model.template_cls()).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)


class FringeQuery(FringeQuerier, BudgetingQuerySet):
    pass


class FringeManager(FringeQuerier, BudgetingManager):
    queryset_class = FringeQuery

    def cleanup(self, instances, **kwargs):
        super().cleanup(instances)
        budgets = set([
            obj.intermittent_budget for obj in instances
            if obj.intermittent_budget is not None
        ])
        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was reestimated.
        for budget in budgets:
            budget_fringes_cache.invalidate(budget)
            budget.mark_updated()

    @signals.disable()
    def bulk_delete(self, instances):
        subaccounts = concat([list(obj.subaccounts.all()) for obj in instances])
        for obj in instances:
            obj.delete()
        self.cleanup(instances)
        self.model.subaccount_cls().objects.bulk_estimate(set(subaccounts))

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

        subaccounts = concat([list(obj.subaccounts.all()) for obj in created])
        self.model.subaccount_cls().objects.bulk_estimate(set(subaccounts))
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        # In the case that the Fringe is added with a flat value, the cutoff
        # is irrelevant.
        for instance in [
                i for i in instances if i.unit == self.model.UNITS.flat]:
            instance.cutoff = None

        self.bulk_update(instances, update_fields)

        subaccounts = concat([
            list(obj.subaccounts.all()) for obj in instances])
        subaccounts, _, _ = self.model.subaccount_cls().objects.bulk_estimate(  # noqa
            instances=set(subaccounts)
        )
        return subaccounts


class BudgetFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_budgets()


class TemplateFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_templates()

from django.db import models
from django.contrib.contenttypes.models import ContentType

from greenbudget.lib.django_utils.models import PrePKBulkCreateQuerySet
from greenbudget.lib.utils import concat

from greenbudget.app import signals

from greenbudget.app.budget.cache import budget_fringes_cache
from greenbudget.app.budgeting.query import BaseBudgetQuerier


class FringeQuerier(BaseBudgetQuerier):

    def for_budgets(self):
        # pylint: disable=no-member
        ctype_id = ContentType.objects.get_for_model(self.budget_cls).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)

    def for_templates(self):
        # pylint: disable=no-member
        ctype_id = ContentType.objects.get_for_model(self.template_cls).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)

    @signals.disable()
    def bulk_delete(self, instances):
        subaccounts = concat([list(obj.subaccounts.all()) for obj in instances])

        for obj in instances:
            obj.delete()

        self.subaccount_cls.objects.bulk_estimate(set(subaccounts))

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was reestimated.
        for budget in set([inst.budget for inst in instances]):
            budget_fringes_cache.invalidate(budget)
            budget.mark_updated()

    @signals.disable()
    def bulk_add(self, instances):
        # It is important to perform the bulk create first, because we need
        # the primary keys for the instances to be hashable.
        created = self.bulk_create(instances, predetermine_pks=True)

        subaccounts = concat([list(obj.subaccounts.all()) for obj in created])
        self.subaccount_cls.objects.bulk_estimate(set(subaccounts))

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was reestimated.
        for budget in set([inst.budget for inst in created]):
            budget_fringes_cache.invalidate(budget)
            budget.mark_updated()
        return created

    @signals.disable()
    def bulk_save(self, instances, update_fields):
        self.bulk_update(instances, update_fields)

        subaccounts = concat([list(obj.subaccounts.all()) for obj in instances])
        subaccounts, _, _ = self.subaccount_cls.objects.bulk_estimate(
            instances=set(subaccounts)
        )

        # We want to update the Budget's `updated_at` property regardless of
        # whether or not the Budget was reestimated.
        for budget in set([inst.budget for inst in instances]):
            budget_fringes_cache.invalidate(budget)
            budget.mark_updated()
        return subaccounts


class FringeQuery(FringeQuerier, PrePKBulkCreateQuerySet):
    pass


class FringeManager(FringeQuerier, models.Manager):
    queryset_class = FringeQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_budgets()


class TemplateFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_templates()

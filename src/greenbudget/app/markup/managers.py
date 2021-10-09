from django.db import models
from django.db.models import Case, Q, When, Value as V, BooleanField

from greenbudget.app.budgeting.utils import get_instance_cls


class MarkupQuerier(object):
    def filter_by_budget(self, budget):
        """
        Since the :obj:`subaccount.models.Markup` is tied to the a
        :obj:`budget.models.Budget` instance only via an eventual parent
        :obj:`account.models.Account` instance, and the relationship between
        :obj:`subaccount.models.Markup` and :obj:`account.models.Account`
        is generic, we have to provide a custom method for filtering the
        :obj:`subaccount.models.Markup`(s) by a budget.
        It is important to note that this method is slow, so it should only
        be used sparingly.
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


class MarkupQuery(MarkupQuerier, models.QuerySet):
    pass


class MarkupManager(MarkupQuerier, models.Manager):
    queryset_class = MarkupQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

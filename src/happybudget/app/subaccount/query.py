from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, Q, When, Value as V, BooleanField

from happybudget.lib.utils import concat
from happybudget.app.tabling.query import (
    OrderedRowQuerier, OrderedRowPolymorphicQuerySet)
from happybudget.app.user.query import ModelOwnershipQuerier


class SubAccountQuerier(OrderedRowQuerier, ModelOwnershipQuerier):
    def filter_by_parent(self, parent):
        return self.filter(
            content_type_id=ContentType.objects.get_for_model(type(parent)).id,
            object_id=parent.pk
        )

    def filter_by_budget(self, budget):
        """
        Since the :obj:`subaccount.models.SubAccount` is tied to the a
        :obj:`budget.models.Budget` instance only via an eventual parent
        :obj:`account.models.Account` instance, and the relationship between
        :obj:`subaccount.models.SubAccount` and :obj:`account.models.Account`
        is generic, we have to provide a custom method for filtering the
        :obj:`subaccount.models.SubAccount`(s) by a budget.

        It is important to note that this method is slow, so it should only
        be used sparingly.
        """
        return self.annotate(
            _has_budget=Case(
                When(self._get_budget_query(budget), then=V(True)),
                default=V(False),
                output_field=BooleanField()
            )
        ).filter(_has_budget=True)

    def _get_subaccount_levels(self, budget):
        subaccount_levels = []
        subaccounts = concat([
            [q[0] for q in account.children.only('pk').values_list('pk')]
            for account in budget.account_cls.objects.filter(parent=budget)
        ])
        while len(subaccounts) != 0:
            subaccount_levels.append(subaccounts)
            subaccounts = concat([
                [q[0] for q in account.children.only('pk').values_list('pk')]
                for account in self.model.objects
                .prefetch_related('children').filter(id__in=subaccounts)
            ])
        return subaccount_levels

    def _get_budget_query(self, budget):
        account_ct = ContentType.objects.get_for_model(budget.account_cls)
        subaccount_ct = ContentType.objects.get_for_model(
            budget.subaccount_cls)
        accounts = [
            q[0] for q in budget.account_cls.objects.filter(parent=budget)
            .only('pk').values_list('pk')
        ]
        query = Q(content_type_id=account_ct) & Q(object_id__in=accounts)
        subaccount_levels = self._get_subaccount_levels(budget)
        for level in subaccount_levels:
            query = query | (
                Q(content_type_id=subaccount_ct) & Q(object_id__in=level))
        return query


class SubAccountQuerySet(
        SubAccountQuerier, OrderedRowPolymorphicQuerySet):
    pass

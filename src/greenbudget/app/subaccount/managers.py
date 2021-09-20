from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, Q, When, Value as V, BooleanField

from polymorphic.managers import PolymorphicManager

from greenbudget.lib.utils import concat
from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet


class SubAccountQuerier(object):
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
            _ongoing=Case(
                When(self._get_case_query(budget), then=V(True)),
                default=V(False),
                output_field=BooleanField()
            )
        ).filter(_ongoing=True)

    @property
    def account_model(self):
        from greenbudget.app.account.models import BudgetAccount, TemplateAccount  # noqa
        from .models import BudgetSubAccount, TemplateSubAccount
        mapping = {
            BudgetSubAccount: BudgetAccount,
            TemplateAccount: TemplateSubAccount
        }
        return mapping[self.model]

    def _get_subaccount_levels(self, budget):
        subaccount_levels = []
        subaccounts = concat([
            [q[0] for q in account.subaccounts.only('pk').values_list('pk')]
            for account in self.account_model.objects.filter(budget=budget)
        ])
        while len(subaccounts) != 0:
            subaccount_levels.append(subaccounts)
            subaccounts = concat([
                [q[0] for q in account.subaccounts.only('pk').values_list('pk')]
                for account in self.model.objects
                .prefetch_related('subaccounts').filter(id__in=subaccounts)
            ])
        return subaccount_levels

    def _get_case_query(self, budget):
        account_ct = ContentType.objects.get_for_model(self.account_model).id
        subaccount_ct = ContentType.objects.get_for_model(self.model).id

        accounts = [
            q[0] for q in self.account_model.objects.filter(budget=budget)
            .only('pk').values_list('pk')
        ]

        query = Q(content_type_id=account_ct) & Q(object_id__in=accounts)
        subaccount_levels = self._get_subaccount_levels(budget)

        for level in subaccount_levels:
            query = query | (
                Q(content_type_id=subaccount_ct) & Q(object_id__in=level))

        return query


class SubAccountQuery(SubAccountQuerier, BulkCreatePolymorphicQuerySet):
    pass


class SubAccountManager(SubAccountQuerier, PolymorphicManager):
    queryset_class = SubAccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

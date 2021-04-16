from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet


class AccountQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(budget__trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(budget__trash=True)


class AccountQuery(AccountQuerier, PolymorphicQuerySet):
    pass


class AccountManager(AccountQuerier, PolymorphicManager):
    queryset_class = AccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

    def create(self, *args, **kwargs):
        from greenbudget.app.subaccount.models import BudgetSubAccount
        template_account = kwargs.pop('template', None)

        if template_account is not None:
            for field in self.model.MAP_FIELDS_FROM_TEMPLATE:
                if field not in kwargs:
                    kwargs[field] = getattr(template_account, field)

        instance = super().create(*args, **kwargs)

        if template_account is not None:
            for template_subaccount in template_account.subaccounts.all():
                BudgetSubAccount.objects.create(
                    parent=instance,
                    budget=instance.budget,
                    template=template_subaccount
                )
        return instance

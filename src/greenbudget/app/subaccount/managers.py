from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet


class SubAccountQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(budget__trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(budget__trash=True)


class SubAccountQuery(SubAccountQuerier, PolymorphicQuerySet):
    pass


class SubAccountManager(SubAccountQuerier, PolymorphicManager):
    queryset_class = SubAccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

    def create(self, *args, **kwargs):
        from .models import BudgetSubAccount
        template_subaccount = kwargs.pop('template', None)

        if template_subaccount is not None:
            for field in self.model.MAP_FIELDS_FROM_TEMPLATE:
                if field not in kwargs:
                    kwargs[field] = getattr(template_subaccount, field)

        instance = super().create(*args, **kwargs)
        if template_subaccount is not None:
            for nested_template_subaccount in template_subaccount.subaccounts.all():  # noqa
                BudgetSubAccount.objects.create(
                    parent=instance,
                    budget=instance.budget,
                    template=nested_template_subaccount
                )
        return instance

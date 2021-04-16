from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet


class BudgetQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(trash=True)


class BudgetQuery(BudgetQuerier, PolymorphicQuerySet):
    pass


class BudgetManager(BudgetQuerier, PolymorphicManager):
    queryset_class = BudgetQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

    def create(self, *args, **kwargs):
        from greenbudget.app.account.models import BudgetAccount
        template = kwargs.pop('template', None)

        if template is not None:
            for field in self.model.MAP_FIELDS_FROM_TEMPLATE:
                if field not in kwargs:
                    kwargs[field] = getattr(template, field)

        instance = super().create(*args, **kwargs)

        if template is not None:
            for template_account in template.accounts.all():
                BudgetAccount.objects.create(
                    template=template_account,
                    budget=instance
                )
        return instance

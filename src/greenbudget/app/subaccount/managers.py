from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet

from greenbudget.app.budget.managers import ModelTemplateManager


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


class BudgetSubAccountManager(ModelTemplateManager(SubAccountManager)):
    template_cls = 'subaccount.TemplateSubAccount'

    def create_from_template(self, *args, **kwargs):
        from .models import BudgetSubAccount

        fringe_map = kwargs.pop('fringe_map', None)
        assert fringe_map is not None, \
            "When creating %s from a template model, a mapping of fringes " \
            "must be provided." % self.model.__name__

        instance = super().create_from_template(*args, **kwargs)
        instance.fringes.set([
            instance.budget.fringes.get(pk=fringe_map[template_fringe.pk])
            for template_fringe in kwargs['template'].fringes.all()
        ])
        for nested_template_subaccount in kwargs['template'].subaccounts.all():
            BudgetSubAccount.objects.create(
                parent=instance,
                budget=instance.budget,
                template=nested_template_subaccount,
                created_by=instance.budget.created_by,
                updated_by=instance.budget.created_by,
                fringe_map=fringe_map
            )
        return instance

    def create(self, *args, **kwargs):
        if 'template' in kwargs:
            return self.create_from_template(*args, **kwargs)
        return super().create(*args, **kwargs)

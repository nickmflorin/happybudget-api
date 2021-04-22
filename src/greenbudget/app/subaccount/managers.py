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
        from greenbudget.app.group.models import BudgetSubAccountGroup
        from .models import BudgetSubAccount

        fringe_map = kwargs.pop('fringe_map', None)
        assert fringe_map is not None, \
            "When creating %s from a template model, a mapping of fringes " \
            "must be provided." % self.model.__name__

        group_map = kwargs.pop('group_map', None)
        assert group_map is not None, \
            "When creating %s from a template model, a mapping of groups " \
            "must be provided." % self.model.__name__

        instance = super().create_from_template(*args, **kwargs)
        instance.fringes.set([
            instance.budget.fringes.get(pk=fringe_map[template_fringe.pk])
            for template_fringe in kwargs['template'].fringes.all()
        ])
        if kwargs['template'].group is not None:
            instance.group = instance.parent.groups.get(
                pk=group_map[kwargs['template'].group.pk])
            instance.save()

        # When creating an Account from a Template, not only do we need to
        # create parallels for the Groups that are associated with the Template
        # Account such that they are associated with the Budget Account, but we
        # need to make sure those Groups are also correctly associated with the
        # new SubAccounts of this Account.  In order to do this, we need to
        # provide a mapping of Group IDs to the manager responsible for creating
        # the SubAccounts.
        group_map = {}
        for template_subaccount_group in kwargs['template'].groups.all():
            group = BudgetSubAccountGroup.objects.create(
                created_by=instance.created_by,
                updated_by=instance.created_by,
                parent=instance,
                template=template_subaccount_group
            )
            group_map[template_subaccount_group.pk] = group.pk

        for nested_template_subaccount in kwargs['template'].subaccounts.all():
            BudgetSubAccount.objects.create(
                parent=instance,
                budget=instance.budget,
                template=nested_template_subaccount,
                created_by=instance.budget.created_by,
                updated_by=instance.budget.created_by,
                fringe_map=fringe_map,
                group_map=group_map
            )
        return instance

    def create(self, *args, **kwargs):
        if 'template' in kwargs:
            return self.create_from_template(*args, **kwargs)
        return super().create(*args, **kwargs)

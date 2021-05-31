from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet

from greenbudget.app.common.managers import (
    ModelTemplateManager, ModelDuplicateManager)


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


class AbstractSubAccountManager(ModelDuplicateManager(SubAccountManager)):
    def _create_group_map(self, instance, ancestor, kwarg_name):
        """
        When either duplicating a :obj:`BudgetSubAccount`/:obj:`TemplateSubAccount`  # noqa
        or deriving a :obj:`BudgetSubAccount` from a :obj:`TemplateSubAccount`,
        not only do we need to create parallels for the :obj:`Group`(s) that are
        associated with the original :obj:`BudgetSubAccount`/:obj:`TemplateSubAccount`  # noqa
        (in the case of duplication) or the :obj:`TemplateSubAccount` (in the
        case of deriving), but we need to make sure that those :obj:`Group`(s)
        are also correctly associated with the new
        :obj:`BudgetSubAccount`(s)/:obj:`TemplateSubAccount`(s) of the new
        :obj:`BudgetSubAccount`/:obj:`TemplateSubAccount`.  In order to do this,
        we need to provide a mapping of :obj:`Group` IDs.
        """
        group_cls = self._get_model_definition_cls('group_cls')
        group_map = {}
        for subaccount_group in ancestor.groups.all():
            kwargs = {
                'created_by': instance.created_by,
                'updated_by': instance.updated_by,
                'parent': instance,
                kwarg_name: subaccount_group
            }
            group = group_cls.objects.create(**kwargs)
            group_map[subaccount_group.pk] = group.pk
        return group_map

    def _create_children(self, instance, ancestor, kwarg_name, **kwargs):
        group_map = self._create_group_map(instance, ancestor, kwarg_name)
        child_cls = self._get_model_definition_cls('child_cls')
        for subaccount in ancestor.subaccounts.all():
            model_kwargs = {
                'created_by': instance.created_by,
                'updated_by': instance.updated_by,
                'budget': instance.budget,
                'parent': instance,
                'group_map': group_map,
                kwarg_name: subaccount
            }
            child_cls.objects.create(**kwargs, **model_kwargs)

    def instantiate_duplicates(self, original, *args, **kwargs):
        pass

    def create_duplicate(self, original, *args, **kwargs):
        """
        Creates a duplicate of the :obj:`BudgetSubAccount` or
        :obj:`TemplateSubAccount` object by deriving all of the properties and
        structure from another :obj:`BudgetSubAccount` or
        :obj:`TemplateSubAccount` instance.
        """
        fringe_map = kwargs.pop('fringe_map', None)
        assert fringe_map is not None, \
            "When duplicating %s from an original model, a mapping of " \
            "fringes must be provided." % self.model.__name__

        group_map = kwargs.pop('group_map', None)
        assert group_map is not None, \
            "When duplicating %s from an original model, a mapping of groups " \
            "must be provided." % self.model.__name__

        instance = super().create_duplicate(original, *args, **kwargs)
        instance.fringes.set([
            instance.budget.fringes.get(pk=fringe_map[template_fringe.pk])
            for template_fringe in original.fringes.all()
        ])
        # If the SubAccount belongs to a Group, use the previously created
        # mapping to associate the new SubAccount with the derived Group.
        if original.group is not None:
            instance.group = instance.parent.groups.get(
                pk=group_map[original.group.pk])
            instance.save()

        self._create_children(
            instance, original, 'original', fringe_map=fringe_map)
        return instance


class BudgetSubAccountManager(ModelTemplateManager(AbstractSubAccountManager)):
    template_cls = 'subaccount.TemplateSubAccount'
    child_cls = 'subaccount.BudgetSubAccount'
    group_cls = 'group.BudgetSubAccountGroup'

    def create_from_template(self, template, *args, **kwargs):
        fringe_map = kwargs.pop('fringe_map', None)
        assert fringe_map is not None, \
            "When creating %s from a template model, a mapping of fringes " \
            "must be provided." % self.model.__name__

        group_map = kwargs.pop('group_map', None)
        assert group_map is not None, \
            "When creating %s from a template model, a mapping of groups " \
            "must be provided." % self.model.__name__

        instance = super().create_from_template(template, *args, **kwargs)
        instance.fringes.set([
            instance.budget.fringes.get(pk=fringe_map[template_fringe.pk])
            for template_fringe in template.fringes.all()
        ])
        # If the SubAccount belongs to a Group, use the previously created
        # mapping to associate the new SubAccount with the derived Group.
        if template.group is not None:
            instance.group = instance.parent.groups.get(
                pk=group_map[template.group.pk])
            instance.save()

        self._create_children(
            instance, template, 'template', fringe_map=fringe_map)
        return instance


class TemplateSubAccountManager(AbstractSubAccountManager):
    child_cls = 'subaccount.TemplateSubAccount'
    group_cls = 'group.TemplateSubAccountGroup'

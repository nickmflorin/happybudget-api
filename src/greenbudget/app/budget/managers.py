from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet

from greenbudget.app.common.managers import (
    ModelTemplateManager, ModelDuplicateManager)


class BudgetQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(trash=True)


class BudgetQuery(BudgetQuerier, PolymorphicQuerySet):
    pass


class BaseBudgetManager(BudgetQuerier, PolymorphicManager):
    queryset_class = BudgetQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetManager(
        ModelDuplicateManager(ModelTemplateManager(BaseBudgetManager))):
    template_cls = 'template.Template'

    def _create_fringe_map(self, instance, ancestor, kwarg_name):
        """
        When either duplicating a :obj:`Budget` or deriving a :obj:`Budget`
        from a :obj:`Template`, not only do we need to create parallels for
        the :obj:`Fringe`(s) that are associated with the original :obj:`Budget`
        (in the case of duplication) or the :obj:`Template` (in the case of
        deriving), but we need to make sure that those :obj:`Fringe`(s) are
        also correctly associated with the new :obj:`SubAccount`(s) of the
        new :obj:`Budget`.  In order to do this, we need to provide a mapping
        of :obj:`Fringe` IDs.
        """
        from greenbudget.app.fringe.models import Fringe

        fringe_map = {}
        for fringe in ancestor.fringes.all():
            kwargs = {
                'created_by': instance.created_by,
                'updated_by': instance.created_by,
                'budget': instance,
                kwarg_name: fringe
            }
            fringe = Fringe.objects.create(**kwargs)
            fringe_map[fringe.id] = fringe.id
        return fringe_map

    def _create_group_map(self, instance, ancestor, kwarg_name):
        """
        When either duplicating a :obj:`Budget` or deriving a :obj:`Budget`
        from a :obj:`Template`, not only do we need to create parallels for
        the :obj:`Group`(s) that are associated with the original :obj:`Budget`
        (in the case of duplication) or the :obj:`Template` (in the case of
        deriving), but we need to make sure that those :obj:`Group`(s) are
        also correctly associated with the new :obj:`Account`(s) of the
        new :obj:`Budget`.  In order to do this, we need to provide a mapping
        of :obj:`Group` IDs.
        """
        from greenbudget.app.group.models import BudgetAccountGroup

        group_map = {}
        for account_group in ancestor.groups.all():
            kwargs = {
                'created_by': instance.created_by,
                'updated_by': instance.created_by,
                'parent': instance,
                kwarg_name: account_group
            }
            group = BudgetAccountGroup.objects.create(**kwargs)
            group_map[account_group.pk] = group.pk
        return group_map

    def _create_children(self, instance, ancestor, kwarg_name, **kwargs):
        from greenbudget.app.account.models import BudgetAccount

        fringe_map = self._create_fringe_map(instance, ancestor, kwarg_name)
        group_map = self._create_group_map(instance, ancestor, kwarg_name)
        for account in ancestor.accounts.all():
            model_kwargs = {
                'created_by': instance.created_by,
                'updated_by': instance.created_by,
                'budget': instance,
                'group_map': group_map,
                'fringe_map': fringe_map,
                kwarg_name: account
            }
            BudgetAccount.objects.create(**kwargs, **model_kwargs)

    def create_duplicate(self, original, *args, **kwargs):
        """
        Creates a duplicate of the :obj:`Budget` object by deriving all of the
        properties and structure from another :obj:`Budget` instance.
        """
        instance = super().create_duplicate(original, *args, **kwargs)
        self._create_children(instance, original, 'original')
        return instance

    def create_from_template(self, template, *args, **kwargs):
        """
        Creates a new :obj:`Budget` object by deriving all of the properties
        and structure from a :obj:`Template` instance.
        """
        instance = super().create_from_template(template, *args, **kwargs)
        self._create_children(instance, template, 'template')
        return instance

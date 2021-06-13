from django.db import transaction

from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet

from greenbudget.app.budget.managers import (
    BudgetQuerier, ModelDuplicateManager)


class TemplateQuerier(BudgetQuerier):

    def user(self, user):
        # pylint: disable=no-member
        return self.filter(community=False, created_by=user)

    def community(self):
        # pylint: disable=no-member
        return self.filter(community=True)


class TemplateQuery(TemplateQuerier, PolymorphicQuerySet):
    pass


class TemplateManager(
        TemplateQuerier, ModelDuplicateManager(PolymorphicManager)):
    queryset_class = TemplateQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

    def _create_fringe_map(self, instance, ancestor):
        """
        When duplicating a :obj:`Template`, not only do we need to create
        parallels for the :obj:`Fringe`(s) that are associated with the
        original :obj:`Template`, but we need to make sure that those
        :obj:`Fringe`(s) are also correctly associated with the new
        :obj:`TemplateAccount`(s) of the new :obj:`Template`.  In order to do
        this, we need to provide a mapping of :obj:`Fringe` IDs.
        """
        from greenbudget.app.fringe.models import Fringe

        fringe_map = {}
        for fringe in ancestor.fringes.all():
            kwargs = {
                'created_by': instance.created_by,
                'updated_by': instance.created_by,
                'budget': instance,
                'original': fringe
            }
            fringe = Fringe.objects.create(**kwargs)
            fringe_map[fringe.id] = fringe.id
        return fringe_map

    def _create_group_map(self, instance, ancestor):
        """
        When duplicating a :obj:`Template`, not only do we need to create
        parallels for the :obj:`Group`(s) that are associated with the original
        :obj:`Template`, but we need to make sure that those :obj:`Group`(s) are
        also correctly associated with the new :obj:`TemplateAccount`(s) of the
        new :obj:`Template`.  In order to do this, we need to provide a mapping
        of :obj:`Group` IDs.
        """
        from greenbudget.app.group.models import TemplateAccountGroup

        group_map = {}
        for account_group in ancestor.groups.all():
            kwargs = {
                'created_by': instance.created_by,
                'updated_by': instance.created_by,
                'parent': instance,
                'original': account_group
            }
            group = TemplateAccountGroup.objects.create(**kwargs)
            group_map[account_group.pk] = group.pk
        return group_map

    def _create_children(self, instance, ancestor, **kwargs):
        from greenbudget.app.account.models import TemplateAccount

        fringe_map = self._create_fringe_map(instance, ancestor)
        group_map = self._create_group_map(instance, ancestor)
        for account in ancestor.accounts.all():
            model_kwargs = {
                'created_by': instance.created_by,
                'updated_by': instance.created_by,
                'budget': instance,
                'group_map': group_map,
                'fringe_map': fringe_map,
                'original': account
            }
            TemplateAccount.objects.create(**kwargs, **model_kwargs)

    def create_duplicate(self, original, *args, **kwargs):
        """
        Creates a duplicate of the :obj:`Template` object by deriving all of the
        properties and structure from another :obj:`Template` instance.
        """
        with transaction.atomic():
            instance = super().create_duplicate(original, *args, **kwargs)
            self._create_children(instance, original)
        return instance

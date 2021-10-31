from polymorphic.managers import PolymorphicManager

from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet
from greenbudget.app.budget.managers import BaseBudgetQuerierMixin
from greenbudget.app.budgeting.query import TemplateQuerier as _TemplateQuerier


class TemplateQuerier(BaseBudgetQuerierMixin, _TemplateQuerier):
    def user(self, user):
        # pylint: disable=no-member
        return self.filter(community=False, created_by=user)

    def community(self):
        # pylint: disable=no-member
        return self.filter(community=True)


class TemplateQuery(TemplateQuerier, BulkCreatePolymorphicQuerySet):
    pass


class TemplateManager(TemplateQuerier, PolymorphicManager):
    queryset_class = TemplateQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

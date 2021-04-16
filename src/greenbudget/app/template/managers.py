from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet


class TemplateQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(trash=True)


class TemplateQuery(TemplateQuerier, PolymorphicQuerySet):
    pass


class TemplateManager(TemplateQuerier, PolymorphicManager):
    queryset_class = TemplateQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

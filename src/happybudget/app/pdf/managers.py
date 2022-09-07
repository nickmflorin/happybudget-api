from happybudget.app import managers
from .query import HeaderTemplateQuerier, HeaderTemplateQuerySet


class HeaderTemplateManager(HeaderTemplateQuerier, managers.Manager):
    queryset_class = HeaderTemplateQuerySet

from happybudget.app import query
from happybudget.app.user.query import ModelOwnershipQuerier


class HeaderTemplateQuerier(ModelOwnershipQuerier):
    pass


class HeaderTemplateQuerySet(query.QuerySet, HeaderTemplateQuerier):
    pass

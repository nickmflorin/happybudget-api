from happybudget.app.tabling.managers import RowManager
from .query import GroupQuerySet, GroupQuerier


class GroupManager(GroupQuerier, RowManager):
    queryset_class = GroupQuerySet


class BudgetGroupManager(GroupManager):
    def get_queryset(self):
        return super().get_queryset().for_budgets()


class TemplateGroupManager(GroupManager):
    def get_queryset(self):
        return super().get_queryset().for_templates()

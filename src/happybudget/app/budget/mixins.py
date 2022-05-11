from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from happybudget.app import permissions, views
from happybudget.app.template.permissions import TemplateObjPermission

from .models import BaseBudget, Budget
from .permissions import IsBudgetDomain, BudgetObjPermission


class BaseBudgetNestedMixin(views.NestedObjectViewMixin):
    """
    A mixin for views that extend off of a budget or template's detail endpoint.
    """
    view_name = "budget"
    budget_queryset_cls = BaseBudget
    budget_permission_classes = [
        BudgetObjPermission(
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]
    permission_classes = [
        permissions.OR(
            permissions.IsFullyAuthenticated,
            permissions.AND(
                IsBudgetDomain(get_nested_obj=lambda view: view.budget),
                permissions.IsPublic(get_nested_obj=lambda view: view.budget),
                permissions.IsSafeRequestMethod,
            )
        )
    ]

    @property
    def instance(self):
        return self.budget

    @cached_property
    def content_type(self):
        return ContentType.objects.get_for_model(type(self.budget))


class BudgetNestedMixin(BaseBudgetNestedMixin):
    """
    A mixin for views that extend off of a budget's detail endpoint.
    """
    budget_permission_classes = [BudgetObjPermission]
    budget_queryset_cls = Budget


class BaseBudgetPublicNestedMixin(BaseBudgetNestedMixin):
    budget_permission_classes = [
        BudgetObjPermission(
            public=True,
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]

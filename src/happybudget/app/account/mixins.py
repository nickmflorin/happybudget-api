from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from happybudget.app import permissions, views
from happybudget.app.budget.permissions import (
    IsBudgetDomain, BudgetObjPermission)
from happybudget.app.template.permissions import TemplateObjPermission

from .models import Account


class AccountNestedMixin(views.NestedObjectViewMixin):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    view_name = 'account'
    account_queryset_cls = Account
    account_permission_classes = [
        BudgetObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='account',
            is_object_applicable=lambda c: c.obj.domain == 'budget'
        ),
        TemplateObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='account',
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]
    permission_classes = [
        permissions.OR(
            permissions.IsFullyAuthenticated,
            permissions.AND(
                IsBudgetDomain(get_nested_obj=lambda view: view.account.budget),
                permissions.IsPublic(
                    get_nested_obj=lambda view: view.account.budget),
                permissions.IsSafeRequestMethod,
            ),
        )
    ]

    @property
    def instance(self):
        return self.account

    @cached_property
    def content_type(self):
        return ContentType.objects.get_for_model(type(self.account))

    @cached_property
    def object_id(self):
        return self.account.pk

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{
            'content_type': self.content_type,
            'object_id': self.object_id
        }}


class AccountPublicNestedMixin(AccountNestedMixin):
    account_permission_classes = [
        BudgetObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='account',
            public=True,
            collaborator_can_destroy=True,
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='account',
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]

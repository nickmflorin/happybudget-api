from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from happybudget.app import permissions, views
from happybudget.app.budget.permissions import (
    IsBudgetDomain, BudgetObjPermission)
from happybudget.app.template.permissions import TemplateObjPermission

from .models import SubAccount


class SubAccountNestedMixin(views.NestedObjectViewMixin):
    """
    A mixin for views that extend off of an subaccount's detail endpoint.
    """
    subaccount_permission_classes = [
        BudgetObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='subaccount',
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='subaccount',
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]
    permission_classes = [
        permissions.OR(
            permissions.IsFullyAuthenticated,
            permissions.AND(
                IsBudgetDomain(
                    get_nested_obj=lambda view: view.subaccount.budget),
                permissions.IsPublic(
                    get_nested_obj=lambda view: view.subaccount.budget),
                permissions.IsSafeRequestMethod,
            ),
        )
    ]
    view_name = 'subaccount'

    def get_subaccount_queryset(self):
        return SubAccount.objects.all()

    @cached_property
    def content_type(self):
        return ContentType.objects.get_for_model(type(self.subaccount))

    @property
    def instance(self):
        return self.subaccount

    @cached_property
    def object_id(self):
        return self.subaccount.pk

    @cached_property
    def budget(self):
        return self.subaccount.budget

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{
            'content_type': self.content_type,
            'object_id': self.object_id
        }}


class SubAccountPublicNestedMixin(SubAccountNestedMixin):
    subaccount_permission_classes = [
        BudgetObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='subaccount',
            public=True,
            collaborator_can_destroy=True,
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='subaccount',
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]

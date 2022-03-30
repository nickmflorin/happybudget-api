from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import mixins, permissions
from greenbudget.app.budgeting.permissions import IsBudgetDomain
from greenbudget.app.collaborator.permissions import IsCollaborator

from .models import SubAccount
from .permissions import (
    SubAccountOwnershipPermission,
    SubAccountProductPermission
)


class SubAccountNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of an subaccount's detail endpoint.
    """
    subaccount_permission_classes = [permissions.AND(
        permissions.OR(
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                SubAccountOwnershipPermission(affects_after=True),
                SubAccountProductPermission(products="__any__"),
            ),
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                IsCollaborator(get_permissioned_obj=lambda obj: obj.budget)
            ),
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        permissions.AND(
            permissions.IsFullyAuthenticated(affects_after=True),
            SubAccountOwnershipPermission(affects_after=True),
            is_object_applicable=lambda c: c.obj.domain == 'template'
        ),
    )]
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
    subaccount_permission_classes = [permissions.AND(
        permissions.OR(
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                SubAccountOwnershipPermission(affects_after=True),
                SubAccountProductPermission(products="__any__"),
            ),
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                IsCollaborator(get_permissioned_obj=lambda obj: obj.budget)
            ),
            permissions.AND(
                permissions.IsSafeRequestMethod,
                permissions.IsPublic(
                    get_permissioned_obj=lambda obj: obj.budget),
            ),
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        permissions.AND(
            permissions.IsFullyAuthenticated(affects_after=True),
            SubAccountOwnershipPermission(affects_after=True),
            is_object_applicable=lambda c: c.obj.domain == 'template'
        ),
    )]

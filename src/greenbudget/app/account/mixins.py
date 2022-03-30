from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import mixins, permissions
from greenbudget.app.budgeting.permissions import IsBudgetDomain
from greenbudget.app.collaborator.permissions import IsCollaborator

from .models import Account
from .permissions import (
    AccountOwnershipPermission,
    AccountProductPermission
)


class AccountNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    account_permission_classes = [permissions.AND(
        permissions.OR(
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                AccountOwnershipPermission(affects_after=True),
                AccountProductPermission(products="__any__"),
            ),
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                IsCollaborator(get_permissioned_obj=lambda obj: obj.budget)
            ),
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        permissions.AND(
            permissions.IsFullyAuthenticated(affects_after=True),
            AccountOwnershipPermission(affects_after=True),
            is_object_applicable=lambda c: c.obj.domain == 'template'
        ),
    )]
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
    view_name = 'account'

    def get_account_queryset(self):
        return Account.objects.all()

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
    account_permission_classes = [permissions.AND(
        permissions.OR(
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                AccountOwnershipPermission(affects_after=True),
                AccountProductPermission(products="__any__"),
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
            AccountOwnershipPermission(affects_after=True),
            is_object_applicable=lambda c: c.obj.domain == 'template'
        ),
    )]

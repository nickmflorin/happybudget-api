from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import mixins, permissions
from greenbudget.app.budgeting.permissions import IsBudgetDomain

from .models import Account
from .permissions import (
    AccountOwnershipPermission,
    AccountProductPermission
)


class AccountNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    account_permission_classes = [
        AccountOwnershipPermission(affects_after=True),
        AccountProductPermission(products="__any__")
    ]
    view_name = 'account'
    account_lookup_field = ("pk", "account_pk")

    def get_account_queryset(self, request):
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


class AccountSharedNestedMixin(AccountNestedMixin):
    account_permission_classes = [
        permissions.OR(
            permissions.AND(
                AccountOwnershipPermission(affects_after=True),
                AccountProductPermission(products="__any__")
            ),
            permissions.AND(
                IsBudgetDomain(get_permissioned_obj=lambda view: view.budget),
                permissions.IsShared(
                    get_permissioned_obj=lambda obj: obj.budget),
            )
        )
    ]
    permission_classes = [
        permissions.OR(
            permissions.IsFullyAuthenticated,
            permissions.AND(
                IsBudgetDomain(get_nested_obj=lambda view: view.account.budget),
                permissions.IsShared(
                    get_nested_obj=lambda view: view.account.budget))
        )
    ]

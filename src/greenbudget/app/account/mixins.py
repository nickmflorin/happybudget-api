from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import mixins

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
        AccountOwnershipPermission,
        AccountProductPermission(products='__any__')
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

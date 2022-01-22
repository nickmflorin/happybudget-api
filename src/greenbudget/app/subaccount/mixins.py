from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app.budgeting.mixins import NestedObjectViewMixin

from .models import SubAccount
from .permissions import (
    SubAccountOwnershipPermission,
    SubAccountProductPermission
)


class SubAccountNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of an subaccount's detail endpoint.
    """
    view_name = 'subaccount'
    subaccount_permission_classes = [
        SubAccountOwnershipPermission,
        SubAccountProductPermission(products='__any__')
    ]
    subaccount_lookup_field = ("pk", "subaccount_pk")

    def get_subaccount_queryset(self, request):
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

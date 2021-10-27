from greenbudget.app.budgeting.mixins import NestedObjectViewMixin

from .models import SubAccount
from .permissions import SubAccountObjPermission


class SubAccountNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of an subaccount's detail endpoint.
    """
    view_name = 'subaccount'
    subaccount_permission_classes = (SubAccountObjPermission, )

    def get_subaccount_queryset(self, request):
        return SubAccount.objects.all()

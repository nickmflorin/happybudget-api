from greenbudget.app.budgeting.mixins import NestedObjectViewMixin

from .models import Account
from .permissions import AccountObjPermission


class AccountNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    account_permission_classes = (AccountObjPermission, )
    view_name = 'account'

    def get_account_queryset(self, request):
        return Account.objects.all()

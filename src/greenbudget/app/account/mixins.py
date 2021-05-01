from greenbudget.app.common.mixins import NestedObjectViewMixin

from .models import Account
from .permissions import AccountObjPermission


class AccountNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    account_permission_classes = (AccountObjPermission, )
    view_name = 'account'

    @property
    def account_polymorphic_instance(self):
        return None

    def get_account_queryset(self, request):
        qs = Account.objects.filter(budget__trash=False)
        if self.account_polymorphic_instance is not None:
            qs = qs.instance_of(self.account_polymorphic_instance)
        return qs

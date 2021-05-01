from greenbudget.app.common.mixins import NestedObjectViewMixin

from .models import SubAccount
from .permissions import SubAccountObjPermission


class SubAccountNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of an subaccount's detail endpoint.
    """
    view_name = 'subaccount'
    permission_classes = (SubAccountObjPermission, )

    @property
    def subaccount_polymorphic_instance(self):
        return None

    def get_subaccount_queryset(self, request):
        qs = SubAccount.objects.filter(budget__trash=False)
        if self.subaccount_polymorphic_instance is not None:
            qs = qs.instance_of(self.subaccount_polymorphic_instance)
        return qs

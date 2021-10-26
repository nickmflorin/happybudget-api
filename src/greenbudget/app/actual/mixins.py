from greenbudget.app.budgeting.mixins import NestedObjectViewMixin

from .models import Actual
from .permissions import ActualObjPermission\



class ActualNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    actual_permission_classes = (ActualObjPermission, )
    view_name = 'actual'

    def get_actual_queryset(self, request):
        return Actual.objects.all()

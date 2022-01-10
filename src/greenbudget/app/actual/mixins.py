from greenbudget.app.budgeting.mixins import NestedObjectViewMixin

from .models import Actual


class ActualNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    view_name = 'actual'
    actual_lookup_field = ("pk", "actual_pk")

    def get_actual_queryset(self, request):
        return Actual.objects.filter(created_by=request.user)

    @property
    def instance(self):
        return self.actual

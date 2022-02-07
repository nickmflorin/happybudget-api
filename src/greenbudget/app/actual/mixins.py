from greenbudget.app import mixins

from .models import Actual


class ActualNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    view_name = 'actual'

    def get_actual_queryset(self):
        return Actual.objects.filter(created_by=self.request.user)

    @property
    def instance(self):
        return self.actual

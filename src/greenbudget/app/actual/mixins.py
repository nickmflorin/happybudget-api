from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from .models import Actual


class ActualNestedMixin(object):
    """
    A mixin for views that extend off of an actual's detail endpoint.
    """
    @property
    def actual_lookup_field(self):
        raise NotImplementedError()

    @cached_property
    def actual(self):
        params = {
            self.actual_lookup_field[0]: (
                self.kwargs[self.actual_lookup_field[1]])
        }
        return get_object_or_404(Actual.objects.all(), **params)

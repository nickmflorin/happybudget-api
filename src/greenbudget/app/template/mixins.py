from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from .models import Template


class TemplateNestedMixin(object):
    """
    A mixin for views that extend off of a template's detail endpoint.
    """
    @property
    def template_lookup_field(self):
        raise NotImplementedError()

    @cached_property
    def template(self):
        params = {
            self.template_lookup_field[0]: (
                self.kwargs[self.template_lookup_field[1]])
        }
        return get_object_or_404(
            self.request.user.budgets.instance_of(Template).active(), **params)

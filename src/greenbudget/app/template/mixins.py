from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import mixins
from greenbudget.app.budget.permissions import BudgetOwnershipPermission

from .models import Template


class TemplateNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of a template's detail endpoint.
    """
    template_permission_classes = [BudgetOwnershipPermission]
    view_name = 'template'
    template_lookup_field = ("pk", "template_pk")

    def get_template_queryset(self, request):
        return Template.objects.all()

    @cached_property
    def content_type(self):
        return ContentType.objects.get_for_model(type(self.template))

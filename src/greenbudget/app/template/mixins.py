from greenbudget.app.common.mixins import NestedObjectViewMixin

from .models import Template
from .permissions import TemplateObjPermission


class TemplateNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of a template's detail endpoint.
    """
    template_permission_classes = [TemplateObjPermission]
    view_name = 'template'

    def get_template_queryset(self, request):
        return Template.objects.all()

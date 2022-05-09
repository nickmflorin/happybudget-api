from happybudget.app import views
from happybudget.app.budget.permissions import BudgetObjPermission
from happybudget.app.template.permissions import TemplateObjPermission

from .models import Markup
from .serializers import MarkupSerializer


class MarkupViewSet(
    views.UpdateModelMixin,
    views.RetrieveModelMixin,
    views.DestroyModelMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) PATCH /markups/<pk>/
    (2) GET /markups/<pk>/
    (3) DELETE /markups/<pk>/
    """
    serializer_class = MarkupSerializer
    permission_classes = [
        BudgetObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='markup',
            collaborator_can_destroy=True,
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='markup',
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]

    def get_serializer_context(self, parent=None):
        context = super().get_serializer_context()
        # The parent object is needed in context in order to update the children
        # of a Markup - but that will only happen in a PATCH request for this
        # view (POST request is handled by another view).
        if self.detail is True and parent is None:
            context['parent'] = self.instance.parent
        if parent is not None:
            # The parent must be explicitly provided in some cases where the
            # Markup instance may be deleted due to a lack of children.
            context['parent'] = parent
        return context

    def get_queryset(self):
        return Markup.objects.all()

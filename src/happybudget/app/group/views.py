from happybudget.app import views
from happybudget.app.budget.permissions import BudgetObjPermission
from happybudget.app.template.permissions import TemplateObjPermission

from .models import Group
from .serializers import GroupSerializer


class GroupViewSet(
    views.UpdateModelMixin,
    views.RetrieveModelMixin,
    views.DestroyModelMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) PATCH /groups/<pk>/
    (2) GET /groups/<pk>/
    (3) DELETE /groups/<pk>/
    """
    queryset_cls = Group
    serializer_class = GroupSerializer
    permission_classes = [
        BudgetObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='group',
            collaborator_can_destroy=True,
            public=True,
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='group',
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # The parent object is needed in context in order to update the children
        # of a Group - but that will only happen in a PATCH request for this
        # view (POST request is handled by another view).
        if self.detail is True:
            obj = self.get_object()
            context['parent'] = obj.parent
        return context

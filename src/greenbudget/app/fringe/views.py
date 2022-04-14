from greenbudget.app import views
from greenbudget.app.budget.permissions import BudgetObjPermission
from greenbudget.app.template.permissions import TemplateObjPermission

from .models import Fringe
from .serializers import FringeSerializer, FringeDetailSerializer


class GenericFringeViewSet(views.GenericViewSet):
    ordering_fields = []
    search_fields = ['name']
    serializer_class = FringeSerializer
    serializer_classes = [
        ({'action__in': ['partial_update', 'create', 'retrieve']},
            FringeDetailSerializer),
    ]


class FringesViewSet(
    views.UpdateModelMixin,
    views.RetrieveModelMixin,
    views.DestroyModelMixin,
    GenericFringeViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /fringes/<pk>/
    (2) PATCH /fringes/<pk>/
    (3) DELETE /fringes/<pk>/
    """
    permission_classes = [
        BudgetObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='fringe',
            collaborator_can_destroy=True,
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='fringe',
            is_object_applicable=lambda c: c.obj.domain == 'template',
        )
    ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.instance.budget)
        return context

    def get_queryset(self):
        return Fringe.objects.all()

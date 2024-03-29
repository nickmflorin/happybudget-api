from happybudget.app import views
from happybudget.app.budget.permissions import BudgetObjPermission
from happybudget.app.template.permissions import TemplateObjPermission

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
    queryset_cls = Fringe
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
        # The Budget of a Fringe will never change via a POST or PATCH request,
        # so including it as context is safe because it will not change as a
        # result of the request data.
        context.update(budget=self.instance.budget)
        return context

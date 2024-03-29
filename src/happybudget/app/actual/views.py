from happybudget.app import views, permissions
from happybudget.app.budget.permissions import BudgetObjPermission
from happybudget.app.io.views import GenericAttachmentViewSet

from .models import Actual, ActualType
from .serializers import (
    ActualSerializer,
    ActualTypeSerializer,
    ActualDetailSerializer
)


class ActualTypeViewSet(views.ListModelMixin, views.GenericViewSet):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /actuals/types/
    """
    serializer_class = ActualTypeSerializer
    queryset_cls = ActualType


class ActualAttachmentViewSet(
    views.NestedObjectViewMixin,
    GenericAttachmentViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/attachments/
    (2) DELETE /actuals/<pk>/attachments/pk/
    (3) POST /actuals/<pk>/attachments/
    """
    view_name = 'actual'
    actual_queryset_cls = Actual
    actual_lookup_url_kwarg = 'actual_pk'
    permission_classes = [
        permissions.IsFullyAuthenticated(affects_after=True),
        permissions.IsOwner(object_name='attachment'),
    ]
    actual_permission_classes = [BudgetObjPermission(
        get_budget=lambda obj: obj.budget,
        object_name='actual',
        # Currently, we do not allow Attachment(s) to be uploaded, deleted or
        # retrieved for instances that belong to another User.
        collaborator=False,
        # Attachments are not applicable for the public domain.
        public=False
    )]

    @property
    def instance(self):
        return self.actual


class GenericActualViewSet(views.GenericViewSet):
    ordering_fields = []
    search_fields = ['description']
    serializer_class = ActualSerializer
    serializer_classes = [
        ({'action__in': ['partial_update', 'create', 'retrieve']},
            ActualDetailSerializer),
    ]


class ActualsViewSet(
    views.UpdateModelMixin,
    views.RetrieveModelMixin,
    views.DestroyModelMixin,
    GenericActualViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/
    (2) PATCH /actuals/<pk>/
    (3) DELETE /actuals/<pk>/
    """
    queryset_cls = Actual
    # Currently, the Actual(s) are not relevant for public permissions on a
    # Budget.
    permission_classes = [BudgetObjPermission(
        get_budget=lambda obj: obj.budget,
        collaborator_can_destroy=True,
        object_name='actual'
    )]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.instance.budget)
        return context

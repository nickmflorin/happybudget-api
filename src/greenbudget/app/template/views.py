from django.db import models
from rest_framework import (
    viewsets, mixins, response, status, decorators, permissions)

from greenbudget.app.account.models import TemplateAccount
from greenbudget.app.account.serializers import TemplateAccountSerializer
from greenbudget.app.account.views import GenericAccountViewSet
from greenbudget.app.budget.decorators import (
    register_all_bulk_operations, BulkAction)
from greenbudget.app.common.permissions import IsAdminOrReadOnly
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.fringe.serializers import FringeSerializer
from greenbudget.app.group.models import TemplateAccountGroup
from greenbudget.app.group.serializers import TemplateAccountGroupSerializer

from .models import Template
from .mixins import TemplateNestedMixin
from .permissions import TemplateObjPermission
from .serializers import TemplateSerializer, TemplateSimpleSerializer


class TemplateGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    TemplateNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /templates/<pk>/groups/
    (2) GET /templates/<pk>/groups/
    """
    lookup_field = 'pk'
    serializer_class = TemplateAccountGroupSerializer
    template_lookup_field = ("pk", "template_pk")

    def get_queryset(self):
        return TemplateAccountGroup.objects.filter(parent=self.template)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.template,
            budget_context=True
        )
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            parent=self.template
        )


class TemplateFringeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    TemplateNestedMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/<pk>/fringes/
    (2) POST /templates/<pk>/fringes/
    """
    lookup_field = 'pk'
    serializer_class = FringeSerializer
    template_lookup_field = ("pk", "template_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            budget=self.template,
            budget_context=True
        )
        return context

    def get_queryset(self):
        return self.template.fringes.all()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            budget=self.template
        )


class TemplateAccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    TemplateNestedMixin,
    GenericAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/<pk>/accounts/
    (2) POST /templates/<pk>/accounts/
    """
    template_lookup_field = ("pk", "template_pk")
    serializer_class = TemplateAccountSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            budget=self.template,
            budget_context=True
        )
        return context

    def get_queryset(self):
        return TemplateAccount.objects.filter(budget=self.template).all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            budget=self.template
        )


class GenericTemplateViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = TemplateSerializer
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            request=self.request,
            user=self.request.user,
        )
        return context

    def get_serializer_class(self):
        if self.action == 'list':
            return TemplateSimpleSerializer
        return TemplateSerializer


@register_all_bulk_operations(
    base_cls=Template,
    filter_qs=lambda context: models.Q(budget=context.instance),
    child_context_indicator='budget_context',
    get_budget=lambda instance: instance,
    # Since the Template is the entity being updated, it will already be
    # included in the response by default.  We do not want to double include it.
    include_budget_in_response=False,
    budget_serializer=TemplateSerializer,
    perform_update=lambda serializer, context: serializer.save(  # noqa
        updated_by=context.request.user
    ),
    perform_create=lambda serializer, context: serializer.save(  # noqa
        created_by=context.request.user,
        updated_by=context.request.user,
        budget=context.instance
    ),
    actions=[
        BulkAction(
            url_path='bulk-{action_name}-accounts',
            child_cls=TemplateAccount,
            child_serializer_cls=TemplateAccountSerializer,
        ),
        BulkAction(
            url_path='bulk-{action_name}-fringes',
            child_cls=Fringe,
            child_serializer_cls=FringeSerializer,
        )
    ]
)
class TemplateViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericTemplateViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/
    (2) POST /templates/
    (3) GET /templates/<pk>/
    (4) PATCH /templates/<pk>/
    (5) DELETE /templates/<pk>/
    (6) PATCH /templates/<pk>/bulk-update-accounts/
    (7) PATCH /templates/<pk>/bulk-create-accounts/
    (8) PATCH /templates/<pk>/bulk-update-actuals/
    (9) PATCH /templates/<pk>/bulk-update-fringes/
    (10) PATCH /templates/<pk>/bulk-create-fringes/
    """
    permission_classes = (
        permissions.IsAuthenticated,
        TemplateObjPermission
    )

    def get_queryset(self):
        qs = Template.objects.all()
        if self.action in ('list', 'create'):
            return qs.user(self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @decorators.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
        instance = self.get_object()
        duplicated = instance.duplicate(request.user)
        return response.Response(
            self.serializer_class(duplicated).data,
            status=status.HTTP_201_CREATED
        )


class TemplateCommunityViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericTemplateViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/community/
    (2) POST /templates/community/
    """
    permission_classes = (
        permissions.IsAuthenticated,
        IsAdminOrReadOnly
    )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(community=True)
        return context

    def get_queryset(self):
        qs = Template.objects.community()
        if not self.request.user.is_staff:
            return qs.filter(hidden=False)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            community=True
        )

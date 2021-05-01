from rest_framework import (
    viewsets, mixins, response, status, decorators, permissions)

from greenbudget.app.account.models import TemplateAccount
from greenbudget.app.account.serializers import (
    TemplateAccountSerializer,
    create_bulk_create_accounts_serializer,
    create_bulk_update_accounts_serializer
)
from greenbudget.app.budget.mixins import TrashModelMixin
from greenbudget.app.common.permissions import IsAdminOrReadOnly
from greenbudget.app.fringe.serializers import (
    FringeSerializer,
    BulkCreateFringesSerializer,
    BulkUpdateFringesSerializer
)
from greenbudget.app.group.models import TemplateAccountGroup
from greenbudget.app.group.serializers import TemplateAccountGroupSerializer

from .models import Template
from .mixins import TemplateNestedMixin
from .permissions import TemplateObjPermission
from .serializers import TemplateSerializer


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
        context.update(parent=self.template)
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
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
        context.update(budget=self.template)
        return context

    def get_queryset(self):
        return self.template.fringes.all()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
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
        qs = Template.objects.active()
        if self.action in ('list', 'create'):
            return qs.user(self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.to_trash()
        return response.Response(status=204)

    def perform_bulk_accounts_change(self, serializer_cls, request):
        instance = self.get_object()
        serializer = serializer_cls(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save(updated_by=request.user)

    @decorators.action(
        detail=True, url_path='bulk-update-accounts', methods=["PATCH"])
    def bulk_update_accounts(self, request, *args, **kwargs):
        serializer_cls = create_bulk_update_accounts_serializer(TemplateAccount)
        instance = self.perform_bulk_accounts_change(serializer_cls, request)
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-create-accounts', methods=["PATCH"])
    def bulk_create_accounts(self, request, *args, **kwargs):
        serializer_cls = create_bulk_create_accounts_serializer(TemplateAccount)
        accounts = self.perform_bulk_accounts_change(serializer_cls, request)
        return response.Response(
            {'data': TemplateAccountSerializer(accounts, many=True).data},
            status=status.HTTP_201_CREATED
        )

    @decorators.action(
        detail=True, url_path='bulk-update-fringes', methods=["PATCH"])
    def bulk_update_fringes(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkUpdateFringesSerializer(
            instance=instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=request.user)
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-create-fringes', methods=["PATCH"])
    def bulk_create_fringes(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkCreateFringesSerializer(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        fringes = serializer.save(updated_by=request.user)
        return response.Response(
            {'data': FringeSerializer(fringes, many=True).data},
            status=status.HTTP_201_CREATED
        )

    @decorators.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
        instance = self.get_object()
        duplicated = Template.objects.create(
            original=instance, created_by=request.user)
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

    def get_queryset(self):
        return Template.objects.active().community()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            community=True
        )


class TemplateTrashViewSet(TrashModelMixin, GenericTemplateViewSet):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/trash/
    (2) GET /templates/trash/<pk>/
    (3) PATCH /templates/trash/<pk>/restore/
    (4) DELETE /templates/trash/<pk>/
    """

    def get_queryset(self):
        return Template.objects.inactive().user(self.request.user)

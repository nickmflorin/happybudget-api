from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property

from rest_framework import viewsets, mixins, response, status

from greenbudget.app.views import filter_by_ids, GenericViewSet
from greenbudget.app.actual.views import GenericActualViewSet
from greenbudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.io.serializers import (
    UploadAttachmentSerializer, AttachmentSerializer)
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSerializer

from .cache import (
    subaccount_subaccounts_cache,
    subaccount_markups_cache,
    subaccount_groups_cache,
    subaccount_instance_cache,
    subaccount_units_cache
)
from .mixins import SubAccountNestedMixin
from .models import (
    SubAccount,
    BudgetSubAccount,
    TemplateSubAccount,
    SubAccountUnit
)
from .serializers import (
    TemplateSubAccountSerializer,
    BudgetSubAccountSerializer,
    BudgetSubAccountDetailSerializer,
    TemplateSubAccountDetailSerializer,
    SubAccountUnitSerializer,
    SubAccountSimpleSerializer
)


@subaccount_units_cache
class SubAccountUnitViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /subaccounts/units/
    """
    serializer_class = SubAccountUnitSerializer

    def get_queryset(self):
        return SubAccountUnit.objects.all()


@filter_by_ids
@subaccount_markups_cache(get_instance_from_view=lambda view: view.subaccount.pk)
class SubAccountMarkupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    SubAccountNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /subaccounts/<pk>/groups/
    (2) GET /subaccounts/<pk>/groups/
    """
    lookup_field = 'pk'
    subaccount_lookup_field = ("pk", "subaccount_pk")
    serializer_class = MarkupSerializer

    def get_queryset(self):
        return Markup.objects.filter(
            content_type=ContentType.objects.get_for_model(type(self.subaccount)),  # noqa
            object_id=self.subaccount.pk,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.subaccount,
            subaccount_context=True
        )
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(type(self.subaccount)),  # noqa
            parent=self.subaccount
        )


@filter_by_ids
@subaccount_groups_cache(get_instance_from_view=lambda view: view.subaccount.pk)
class SubAccountGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    SubAccountNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /subaccounts/<pk>/groups/
    (2) GET /subaccounts/<pk>/groups/
    """
    lookup_field = 'pk'
    subaccount_lookup_field = ("pk", "subaccount_pk")
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            content_type=ContentType.objects.get_for_model(type(self.subaccount)),  # noqa
            object_id=self.subaccount.pk,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.subaccount,
            subaccount_context=True
        )
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(
                type(self.subaccount))
        )


@filter_by_ids
class SubAccountActualsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    SubAccountNestedMixin,
    GenericActualViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/actuals/
    (2) POST /subaccounts/<pk>/actuals/

    Note:
    ----
    This view is currently not cached because it is not in use.  If we do start
    using it by the FE, we should cache it.
    """
    subaccount_lookup_field = ("pk", "subaccount_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            budget=self.subaccount.budget,
            subaccount_context=True
        )
        return context

    def get_queryset(self):
        return self.subaccount.actuals.all()

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(type(self.subaccount)),  # noqa
            budget=self.subaccount.budget,
        )


class SubAccountAttachmentViewSet(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    SubAccountNestedMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/attachments/
    (2) DELETE /subaccounts/<pk>/attachments/pk/
    (3) POST /subaccounts/<pk>/attachments/
    """
    subaccount_lookup_field = ("pk", "subaccount_pk")
    serializer_class = AttachmentSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return self.subaccount.attachments.all()

    def create(self, request, *args, **kwargs):
        serializer = UploadAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(created_by=request.user)
        self.subaccount.attachments.add(attachment)
        root_serializer_class = self.get_serializer_class()
        return response.Response(
            root_serializer_class(instance=attachment).data,
            status=status.HTTP_200_OK
        )


class GenericSubAccountViewSet(GenericViewSet):
    lookup_field = 'pk'
    ordering_fields = []
    search_fields = ['identifier', 'description']
    serializer_classes = (
        ({'is_simple': True}, SubAccountSimpleSerializer),
        ({'instance_cls.domain': 'template'}, [
            (
                {'action__in': ('create', 'partial_update', 'retrieve')},
                TemplateSubAccountDetailSerializer
            ),
            TemplateSubAccountSerializer
        ]),
        ({'instance_cls.domain': 'budget'}, [
            (
                {'action__in': ('create', 'partial_update', 'retrieve')},
                BudgetSubAccountDetailSerializer
            ),
            BudgetSubAccountSerializer
        ]),
    )


@register_bulk_operations(
    base_cls=lambda context: context.view.instance_cls,
    child_context_indicator='subaccount_context',
    get_budget=lambda instance: instance.budget,
    child_context=lambda context: {"parent": context.instance},
    actions=[
        BulkDeleteAction(
            url_path='bulk-{action_name}-markups',
            child_cls=Markup,
            filter_qs=lambda context: models.Q(
                content_type=ContentType.objects.get_for_model(context.instance),
                object_id=context.instance.pk
            ),
        ),
        BulkAction(
            url_path='bulk-{action_name}-subaccounts',
            child_cls=lambda context: context.view.child_instance_cls,
            child_serializer_cls=lambda context: context.view.child_serializer_cls,  # noqa
            filter_qs=lambda context: models.Q(
                object_id=context.instance.pk,
                content_type=ContentType.objects.get_for_model(
                    context.view.instance_cls)
            ),
            perform_update=lambda serializer, context: serializer.save(
                updated_by=context.request.user
            ),
            perform_create=lambda serializer, context: serializer.save(  # noqa
                created_by=context.request.user,
                updated_by=context.request.user,
                parent=context.instance,
            )
        )
    ]
)
@subaccount_instance_cache(get_instance_from_view=lambda view: view.instance.pk)
class SubAccountViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericSubAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/
    (2) PATCH /subaccounts/<pk>/
    (3) DELETE /subaccounts/<pk>/
    (4) PATCH /subaccounts/<pk>/bulk-update-subaccounts/
    (5) PATCH /subaccounts/<pk>/bulk-create-subaccounts/
    """
    throttle_classes = []

    @cached_property
    def instance(self):
        return self.get_object()

    @property
    def instance_cls(self):
        return type(self.instance)

    @property
    def child_instance_cls(self):
        if self.instance_cls is BudgetSubAccount:
            return BudgetSubAccount
        return TemplateSubAccount

    @property
    def child_serializer_cls(self):
        if self.child_instance_cls is BudgetSubAccount:
            return BudgetSubAccountDetailSerializer
        return TemplateSubAccountDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance.parent)
        return context

    def get_queryset(self):
        return SubAccount.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


@filter_by_ids
@subaccount_subaccounts_cache(
    get_instance_from_view=lambda view: view.subaccount.pk)
class SubAccountRecursiveViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    SubAccountNestedMixin,
    GenericSubAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/subaccounts
    (2) POST /subaccounts/<pk>/subaccounts
    """
    subaccount_lookup_field = ("pk", "subaccount_pk")

    @cached_property
    def instance_cls(self):
        return type(self.subaccount)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.subaccount,
            subaccount_context=True
        )
        return context

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(type(self.subaccount))
        qs = type(self.subaccount).objects.filter(
            object_id=self.subaccount.pk,
            content_type=content_type,
        )
        if self.instance_cls is not TemplateSubAccount:
            qs = qs.prefetch_related('attachments')
        return qs

    def perform_create(self, serializer):
        return serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(type(self.subaccount)),  # noqa
        )

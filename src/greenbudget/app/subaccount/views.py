from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property

from rest_framework import viewsets, mixins

from greenbudget.app.actual.views import GenericActualViewSet
from greenbudget.app.budget.decorators import (
    register_all_bulk_operations, BulkAction)
from greenbudget.app.group.models import (
    BudgetSubAccountGroup,
    TemplateSubAccountGroup
)
from greenbudget.app.group.serializers import (
    BudgetSubAccountGroupSerializer,
    TemplateSubAccountGroupSerializer
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
    SubAccountUnitSerializer
)


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

    @cached_property
    def instance_cls(self):
        mapping = {
            BudgetSubAccount: BudgetSubAccountGroup,
            TemplateSubAccount: TemplateSubAccountGroup
        }
        return mapping[type(self.subaccount)]

    def get_serializer_class(self):
        mapping = {
            BudgetSubAccountGroup: BudgetSubAccountGroupSerializer,
            TemplateSubAccountGroup: TemplateSubAccountGroupSerializer
        }
        return mapping[self.instance_cls]

    def get_queryset(self):
        return self.instance_cls.objects.filter(
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
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(self.instance_cls),
            parent=self.subaccount
        )


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
    """
    subaccount_lookup_field = ("pk", "subaccount_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            budget=self.subaccount.budget,
            subaccount=self.subaccount,
            subaccount_context=True
        )
        return context

    def get_queryset(self):
        return self.subaccount.actuals.all()

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            subaccount=self.subaccount,
            budget=self.subaccount.budget,
        )


class GenericSubAccountViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']


@register_all_bulk_operations(
    base_cls=lambda context: context.view.instance_cls,
    child_context=lambda context: {
        'budget': context.instance.budget,
        'subaccount_context': True
    },
    actions=[
        BulkAction(
            url_path='bulk-{action_name}-subaccounts',
            child_cls=lambda context: context.view.child_instance_cls,
            child_serializer_cls=lambda context: context.view.child_serializer_cls,  # noqa
            filter_qs=lambda context: models.Q(
                budget=context.instance.budget,
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
                budget=context.instance.budget
            )
        )
    ]
)
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
    def instance_cls(self):
        instance = self.get_object()
        return type(instance)

    @property
    def child_instance_cls(self):
        if self.instance_cls is BudgetSubAccount:
            return BudgetSubAccount
        return TemplateSubAccount

    @property
    def child_serializer_cls(self):
        if self.child_instance_cls is BudgetSubAccount:
            return BudgetSubAccountSerializer
        return TemplateSubAccountSerializer

    def get_queryset(self):
        return SubAccount.objects.filter(budget__trash=False)

    def get_serializer_class(self):
        if self.instance_cls is TemplateSubAccount:
            return TemplateSubAccountSerializer
        return BudgetSubAccountSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


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

    def get_serializer_class(self):
        if self.instance_cls is TemplateSubAccount:
            return TemplateSubAccountSerializer
        return BudgetSubAccountSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.subaccount,
            subaccount_context=True
        )
        return context

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(type(self.subaccount))
        return type(self.subaccount).objects.filter(
            object_id=self.subaccount.pk,
            content_type=content_type,
        )

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(type(self.subaccount)),  # noqa
            parent=self.subaccount,
            budget=self.subaccount.budget
        )

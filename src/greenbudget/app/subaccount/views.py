from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app import views, mixins, permissions
from greenbudget.app.budget.serializers import BudgetSerializer
from greenbudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.io.views import GenericAttachmentViewSet
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSerializer
from greenbudget.app.template.serializers import TemplateSerializer

from .cache import (
    subaccount_children_cache,
    subaccount_markups_cache,
    subaccount_groups_cache,
    subaccount_instance_cache,
    subaccount_units_cache
)
from .mixins import SubAccountNestedMixin, SubAccountPublicNestedMixin
from .models import SubAccount, TemplateSubAccount, SubAccountUnit
from .permissions import (
    SubAccountProductPermission,
    SubAccountOwnershipPermission
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
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /subaccounts/units/
    """
    serializer_class = SubAccountUnitSerializer
    permission_classes = [
        permissions.OR(
            permissions.IsFullyAuthenticated,
            # Since there is no public object here, this will simply check if
            # there is a valid public token in the request.
            permissions.IsPublic
        )
    ]

    def get_queryset(self):
        return SubAccountUnit.objects.all()


@views.filter_by_ids
@subaccount_markups_cache
class SubAccountMarkupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    SubAccountPublicNestedMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /subaccounts/<pk>/groups/
    (2) GET /subaccounts/<pk>/groups/
    """
    serializer_class = MarkupSerializer

    def get_queryset(self):
        return Markup.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance)
        return context


@views.filter_by_ids
@subaccount_groups_cache
class SubAccountGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    SubAccountPublicNestedMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /subaccounts/<pk>/groups/
    (2) GET /subaccounts/<pk>/groups/
    """
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance)
        return context


class SubAccountAttachmentViewSet(
    SubAccountNestedMixin,
    GenericAttachmentViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/attachments/
    (2) DELETE /subaccounts/<pk>/attachments/pk/
    (3) POST /subaccounts/<pk>/attachments/
    """
    pass


class GenericSubAccountViewSet(views.GenericViewSet):
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
    get_budget=lambda instance: instance.budget,
    child_context=lambda context: {"parent": context.instance},
    budget_serializer=lambda context: context.view.budget_serializer,
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
            url_path='bulk-{action_name}-children',
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
@subaccount_instance_cache
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
    (4) PATCH /subaccounts/<pk>/bulk-update-children/
    (5) PATCH /subaccounts/<pk>/bulk-create-children/
    """
    permission_classes = [
        permissions.OR(
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                SubAccountOwnershipPermission(affects_after=True),
                SubAccountProductPermission(products="__any__")
            ),
            permissions.AND(
                permissions.IsPublic(
                    get_permissioned_obj=lambda obj: obj.budget),
                permissions.IsSafeRequestMethod,
                is_object_applicable=lambda c: c.obj.domain == "budget"
            )
        )
    ]

    @property
    def child_instance_cls(self):
        return self.instance_cls.child_instance_cls

    @property
    def budget_serializer(self):
        return {
            'budget': BudgetSerializer,
            'template': TemplateSerializer
        }[self.instance_cls.domain]

    @property
    def child_serializer_cls(self):
        return {
            'budget': BudgetSubAccountDetailSerializer,
            'template': TemplateSubAccountDetailSerializer
        }[self.instance_cls.domain]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance.parent)
        return context

    def get_queryset(self):
        return SubAccount.objects.all()


@views.filter_by_ids
@subaccount_children_cache
class SubAccountRecursiveViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    SubAccountPublicNestedMixin,
    GenericSubAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/children
    (2) POST /subaccounts/<pk>/children
    """

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance)
        return context

    def get_queryset(self):
        qs = type(self.instance).objects.filter(
            object_id=self.object_id,
            content_type=self.content_type
        )
        if self.instance_cls is not TemplateSubAccount:
            qs = qs.prefetch_related('attachments')
        return qs.order_with_groups()

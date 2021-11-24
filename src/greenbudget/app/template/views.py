from django.contrib.contenttypes.models import ContentType
from django.db import models
from rest_framework import response, status, decorators

from greenbudget.app import views, mixins
from greenbudget.app.account.models import TemplateAccount
from greenbudget.app.account.serializers import TemplateAccountSerializer
from greenbudget.app.account.views import GenericAccountViewSet
from greenbudget.app.budget.cache import (
    budget_groups_cache,
    budget_accounts_cache,
    budget_markups_cache,
    budget_instance_cache,
    budget_fringes_cache
)
from greenbudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from greenbudget.app.authentication.permissions import IsAdminOrReadOnly
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.fringe.serializers import FringeSerializer
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSerializer

from .models import Template
from .mixins import TemplateNestedMixin
from .permissions import TemplateObjPermission
from .serializers import TemplateSerializer, TemplateSimpleSerializer


@views.filter_by_ids
@budget_markups_cache(get_instance_from_view=lambda view: view.template.pk)
class TemplateMarkupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    TemplateNestedMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /templates/<pk>/markups/
    (2) GET /templates/<pk>/markups/
    """
    serializer_class = MarkupSerializer

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'parent': self.template}}

    def get_queryset(self):
        return Markup.objects.filter(
            content_type=ContentType.objects.get_for_model(Template),
            object_id=self.template.pk
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.template)
        return context


@views.filter_by_ids
@budget_groups_cache(get_instance_from_view=lambda view: view.template.pk)
class TemplateGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    TemplateNestedMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /templates/<pk>/groups/
    (2) GET /templates/<pk>/groups/
    """
    serializer_class = GroupSerializer

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{
            'content_type': self.content_type,
            'object_id': self.budget.pk
        }}

    def get_queryset(self):
        return Group.objects.filter(
            content_type=self.content_type,
            object_id=self.template.pk
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.template)
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            content_type=self.content_type,
            object_id=self.template.pk
        )


@views.filter_by_ids
@budget_fringes_cache(get_instance_from_view=lambda view: view.template.pk)
class TemplateFringeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    TemplateNestedMixin,
    views.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/<pk>/fringes/
    (2) POST /templates/<pk>/fringes/
    """
    serializer_class = FringeSerializer

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'budget': self.template}}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.template)
        return context

    def get_queryset(self):
        return self.template.fringes.all()


@views.filter_by_ids
@budget_accounts_cache(get_instance_from_view=lambda view: view.template.pk)
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
    instance_cls = Template

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'parent': self.template}}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.template)
        return context

    def get_queryset(self):
        return TemplateAccount.objects.filter(parent=self.template).all()


class GenericTemplateViewSet(views.GenericViewSet):
    serializer_class = TemplateSerializer
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return TemplateSimpleSerializer
        return TemplateSerializer


@register_bulk_operations(
    base_cls=Template,
    get_budget=lambda instance: instance,
    # Since the Template is the entity being updated, it will already be
    # included in the response by default.  We do not want to double include it.
    include_budget_in_response=False,
    child_context=lambda context: {"parent": context.instance},
    budget_serializer=TemplateSerializer,
    perform_update=lambda serializer, context: serializer.save(  # noqa
        updated_by=context.request.user
    ),
    actions=[
        BulkAction(
            url_path='bulk-{action_name}-accounts',
            child_cls=TemplateAccount,
            child_serializer_cls=TemplateAccountSerializer,
            filter_qs=lambda context: models.Q(parent=context.instance),
            perform_create=lambda serializer, context: serializer.save(  # noqa
                created_by=context.request.user,
                updated_by=context.request.user,
                parent=context.instance
            ),
        ),
        BulkDeleteAction(
            url_path='bulk-{action_name}-markups',
            child_cls=Markup,
            filter_qs=lambda context: models.Q(
                content_type=ContentType.objects.get_for_model(Template),
                object_id=context.instance.pk
            ),
        ),
        BulkAction(
            url_path='bulk-{action_name}-fringes',
            child_cls=Fringe,
            child_serializer_cls=FringeSerializer,
            filter_qs=lambda context: models.Q(budget=context.instance),
            perform_create=lambda serializer, context: serializer.save(  # noqa
                created_by=context.request.user,
                updated_by=context.request.user,
                budget=context.instance
            ),
        )
    ]
)
@budget_instance_cache(get_instance_from_view=lambda view: view.instance.pk)
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
    extra_permission_classes = (TemplateObjPermission, )

    def get_queryset(self):
        qs = Template.objects.all()
        if self.action in ('list', 'create'):
            return qs.user(self.request.user)
        return qs

    @decorators.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
        duplicated = type(self.instance).objects.duplicate(
            self.instance, request.user)
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
    permission_classes = (IsAdminOrReadOnly, )

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'community': True}}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(community=True)
        return context

    def get_queryset(self):
        qs = Template.objects.community()
        if not self.request.user.is_staff:
            return qs.filter(hidden=False)
        return qs

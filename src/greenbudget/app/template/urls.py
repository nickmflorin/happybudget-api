from django.urls import path, include
from rest_framework_nested import routers

from greenbudget.lib.drf.router import combine_routers

from .views import (
    TemplateViewSet,
    TemplateFringeViewSet,
    TemplateGroupViewSet,
    TemplateAccountViewSet,
    TemplateCommunityViewSet,
    TemplateMarkupViewSet
)

app_name = "template"

router = routers.SimpleRouter()
router.register(
    r'community', TemplateCommunityViewSet, basename='community')
router.register(r'', TemplateViewSet, basename='template')

template_fringes_router = routers.NestedSimpleRouter(
    router, r'', lookup='template')
template_fringes_router.register(
    r'fringes', TemplateFringeViewSet, basename='fringe')

template_groups_router = routers.NestedSimpleRouter(
    router, r'', lookup='template')
template_groups_router.register(
    r'groups', TemplateGroupViewSet, basename='group')

template_markup_router = routers.NestedSimpleRouter(
    router, r'', lookup='template')
template_markup_router.register(
    r'markups', TemplateMarkupViewSet, basename='markup')

template_children_router = routers.SimpleRouter()
template_children_router.register(
    r'', TemplateAccountViewSet, basename='child')

urlpatterns = combine_routers(
    router,
    template_fringes_router,
    template_markup_router,
    template_groups_router,
) + [
    path('<int:template_pk>/', include([
        path('children/', include(template_children_router.urls)),
    ]))
]

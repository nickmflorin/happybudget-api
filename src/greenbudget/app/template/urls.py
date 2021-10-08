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
    r'community', TemplateCommunityViewSet, basename='template-community')
router.register(r'', TemplateViewSet, basename='template')

template_fringes_router = routers.NestedSimpleRouter(
    router, r'', lookup='template')
template_fringes_router.register(
    r'fringes', TemplateFringeViewSet, basename='template-fringe')

template_groups_router = routers.NestedSimpleRouter(
    router, r'', lookup='template')
template_groups_router.register(
    r'groups', TemplateGroupViewSet, basename='template-group')

template_markup_router = routers.NestedSimpleRouter(
    router, r'', lookup='template')
template_markup_router.register(
    r'markups', TemplateMarkupViewSet, basename='template-markup')

template_accounts_router = routers.SimpleRouter()
template_accounts_router.register(
    r'', TemplateAccountViewSet, basename='template-account')

urlpatterns = combine_routers(
    router,
    template_fringes_router,
    template_markup_router,
    template_groups_router,
) + [
    path('<int:template_pk>/', include([
        path('accounts/', include(template_accounts_router.urls)),
    ]))
]

from django.urls import path, include
from rest_framework import routers

from .views import (
    TemplateViewSet,
    TemplateTrashViewSet,
    TemplateFringeViewSet,
    TemplateGroupViewSet,
    TemplateAccountViewSet,
    TemplateCommunityViewSet
)

app_name = "template"

router = routers.SimpleRouter()
router.register(
    r'community', TemplateCommunityViewSet, basename='template-community')
router.register(r'trash', TemplateTrashViewSet, basename='template-trash')
router.register(r'', TemplateViewSet, basename='template')

template_fringes_router = routers.SimpleRouter()
template_fringes_router.register(
    r'', TemplateFringeViewSet, basename='template-fringe')

template_groups_router = routers.SimpleRouter()
template_groups_router.register(
    r'', TemplateGroupViewSet, basename='template-group')

template_accounts_router = routers.SimpleRouter()
template_accounts_router.register(
    r'', TemplateAccountViewSet, basename='template-account')

urlpatterns = router.urls + [
    path('<int:template_pk>/', include([
        path('accounts/', include(template_accounts_router.urls)),
        path('groups/', include(template_groups_router.urls)),
        path('fringes/', include(template_fringes_router.urls)),
    ]))
]

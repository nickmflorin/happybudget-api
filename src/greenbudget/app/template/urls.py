from django.urls import path, include
from rest_framework import routers

from greenbudget.app.account.urls import template_accounts_router

from .views import (
    TemplateViewSet,
    TemplateTrashViewSet,
    TemplateFringeViewSet,
    TemplateGroupViewSet
)

app_name = "template"

router = routers.SimpleRouter()
router.register(r'trash', TemplateTrashViewSet, basename='template-trash')
router.register(r'', TemplateViewSet, basename='template')

template_fringes_router = routers.SimpleRouter()
template_fringes_router.register(
    r'', TemplateFringeViewSet, basename='template-fringe')

template_groups_router = routers.SimpleRouter()
template_groups_router.register(
    r'', TemplateGroupViewSet, basename='template-group')

urlpatterns = router.urls + [
    path('<int:template_pk>/', include([
        path('accounts/', include(template_accounts_router.urls)),
        path('groups/', include(template_groups_router.urls)),
        path('fringes/', include(template_fringes_router.urls)),
    ]))
]

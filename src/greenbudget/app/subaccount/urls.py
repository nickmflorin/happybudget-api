from django.urls import path, include
from rest_framework import routers

from .views import (
    SubAccountViewSet,
    SubAccountRecursiveViewSet,
    SubAccountGroupViewSet,
    SubAccountMarkupViewSet,
    SubAccountUnitViewSet,
    SubAccountActualsViewSet,
    SubAccountAttachmentViewSet
)

app_name = "subaccount"

subaccount_subaccounts_router = routers.SimpleRouter()
subaccount_subaccounts_router.register(
    r'', SubAccountRecursiveViewSet, basename='subaccount')

subaccount_actuals_router = routers.SimpleRouter()
subaccount_actuals_router.register(
    r'', SubAccountActualsViewSet, basename='actual')

subaccount_groups_router = routers.SimpleRouter()
subaccount_groups_router.register(
    r'',
    SubAccountGroupViewSet,
    basename='group'
)

subaccount_markup_router = routers.SimpleRouter()
subaccount_markup_router.register(
    r'',
    SubAccountMarkupViewSet,
    basename='markup'
)

subaccount_attachments_router = routers.SimpleRouter()
subaccount_attachments_router.register(
    r'',
    SubAccountAttachmentViewSet,
    basename='attachment'
)

router = routers.SimpleRouter()
router.register(r'units', SubAccountUnitViewSet, basename='unit')
router.register(r'', SubAccountViewSet, basename='subaccount')

urlpatterns = router.urls + [
    path('<int:subaccount_pk>/', include([
        path('subaccounts/', include(subaccount_subaccounts_router.urls)),
        path('attachments/', include(subaccount_attachments_router.urls)),
        path('actuals/', include(subaccount_actuals_router.urls)),
        path('groups/', include(subaccount_groups_router.urls)),
        path('markups/', include(subaccount_markup_router.urls)),
    ]))
]

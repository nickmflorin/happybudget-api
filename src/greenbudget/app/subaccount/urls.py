from django.urls import path, include
from rest_framework import routers

from greenbudget.app.comment.urls import subaccount_comments_urlpatterns
from greenbudget.app.history.urls import (
    subaccount_subaccounts_history_urlpatterns,
    subaccount_history_urlpatterns
)
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
subaccount_subaccounts_urlpatterns = subaccount_subaccounts_router.urls + [
    path('history/', include(subaccount_subaccounts_history_urlpatterns)),
]

subaccount_actuals_router = routers.SimpleRouter()
subaccount_actuals_router.register(
    r'', SubAccountActualsViewSet, basename='actual')

subaccount_groups_router = routers.SimpleRouter()
subaccount_groups_router.register(
    r'', SubAccountGroupViewSet,
    basename='subaccount-group'
)

subaccount_markup_router = routers.SimpleRouter()
subaccount_markup_router.register(
    r'', SubAccountMarkupViewSet,
    basename='subaccount-markup'
)

subaccount_attachments_router = routers.SimpleRouter()
subaccount_attachments_router.register(
    r'', SubAccountAttachmentViewSet,
    basename='subaccount-attachment'
)

router = routers.SimpleRouter()
router.register(r'units', SubAccountUnitViewSet, basename='subaccount-unit')
router.register(r'', SubAccountViewSet, basename='subaccount')

urlpatterns = router.urls + [
    path('<int:subaccount_pk>/', include([
        path('subaccounts/', include(subaccount_subaccounts_urlpatterns)),
        path('attachments/', include(subaccount_attachments_router.urls)),
        path('actuals/', include(subaccount_actuals_router.urls)),
        path('comments/', include(subaccount_comments_urlpatterns)),
        path('history/', include(subaccount_history_urlpatterns)),
        path('groups/', include(subaccount_groups_router.urls)),
        path('markups/', include(subaccount_markup_router.urls)),
    ]))
]

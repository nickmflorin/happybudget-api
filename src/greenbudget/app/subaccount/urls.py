from django.urls import path, include
from rest_framework import routers

from greenbudget.app.actual.urls import subaccount_actuals_urlpatterns
from greenbudget.app.comment.urls import subaccount_comments_urlpatterns
from greenbudget.app.history.urls import (
    account_subaccounts_history_urlpatterns,
    subaccount_subaccounts_history_urlpatterns,
    subaccount_history_urlpatterns
)
from .views import (
    SubAccountViewSet,
    AccountSubAccountViewSet,
    SubAccountRecursiveViewSet,
    SubAccountSubAccountGroupViewSet,
    AccountSubAccountGroupViewSet,
    SubAccountGroupViewSet
)


app_name = "subaccount"

account_subaccounts_router = routers.SimpleRouter()
account_subaccounts_router.register(
    r'', AccountSubAccountViewSet, basename='subaccount')
account_subaccounts_urlpatterns = account_subaccounts_router.urls + [
    path('history/', include(account_subaccounts_history_urlpatterns)),
]

subaccount_subaccounts_router = routers.SimpleRouter()
subaccount_subaccounts_router.register(
    r'', SubAccountRecursiveViewSet, basename='subaccount')
subaccount_subaccounts_urlpatterns = subaccount_subaccounts_router.urls + [
    path('history/', include(subaccount_subaccounts_history_urlpatterns)),
]

subaccount_groups_router = routers.SimpleRouter()
subaccount_groups_router.register(
    r'', SubAccountSubAccountGroupViewSet,
    basename='subaccount-subaccount-group'
)

account_groups_router = routers.SimpleRouter()
account_groups_router.register(
    r'', AccountSubAccountGroupViewSet,
    basename='account-subaccount-group'
)
account_subaccounts_groups_urlpatterns = account_groups_router.urls

router = routers.SimpleRouter()
router.register(r'', SubAccountViewSet, basename='subaccount')
router.register(
    r'groups',
    SubAccountGroupViewSet,
    basename='subaccount-group'
)

urlpatterns = router.urls + [
    path('<int:subaccount_pk>/', include([
        path('subaccounts/', include(subaccount_subaccounts_urlpatterns)),
        path('actuals/', include(subaccount_actuals_urlpatterns)),
        path('comments/', include(subaccount_comments_urlpatterns)),
        path('history/', include(subaccount_history_urlpatterns)),
        path('groups/', include(subaccount_groups_router.urls)),
    ]))
]

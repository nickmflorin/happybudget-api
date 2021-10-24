from rest_framework import routers

from .views import (
    AccountsHistoryViewSet,
    AccountHistoryViewSet,
    AccountSubAccountsHistoryViewSet,
    SubAccountSubAccountsHistoryViewSet,
    SubAccountHistoryViewSet
)

app_name = "history"

accounts_history_router = routers.SimpleRouter()
accounts_history_router.register(
    r'', AccountsHistoryViewSet, basename='history')
accounts_history_urlpatterns = accounts_history_router.urls

account_history_router = routers.SimpleRouter()
account_history_router.register(r'', AccountHistoryViewSet, basename='history')
account_history_urlpatterns = account_history_router.urls

account_subaccounts_history_router = routers.SimpleRouter()
account_subaccounts_history_router.register(
    r'', AccountSubAccountsHistoryViewSet, basename='history')
account_subaccounts_history_urlpatterns = account_subaccounts_history_router.urls  # noqa

subaccount_subaccounts_history_router = routers.SimpleRouter()
subaccount_subaccounts_history_router.register(
    r'', SubAccountSubAccountsHistoryViewSet, basename='history')
subaccount_subaccounts_history_urlpatterns = subaccount_subaccounts_history_router.urls  # noqa

subaccount_history_router = routers.SimpleRouter()
subaccount_history_router.register(
    r'', SubAccountHistoryViewSet, basename='history')
subaccount_history_urlpatterns = subaccount_history_router.urls

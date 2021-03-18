from rest_framework import routers

from .views import (
    AccountsHistoryViewSet, AccountHistoryViewSet, SubAccountsHistoryViewSet,
    SubAccountHistoryViewSet)

app_name = "history"

accounts_history_router = routers.SimpleRouter()
accounts_history_router.register(
    r'', AccountsHistoryViewSet, basename='history')
accounts_history_urlpatterns = accounts_history_router.urls

account_history_router = routers.SimpleRouter()
account_history_router.register(r'', AccountHistoryViewSet, basename='history')
account_history_urlpatterns = account_history_router.urls

subaccounts_history_router = routers.SimpleRouter()
subaccounts_history_router.register(
    r'', SubAccountsHistoryViewSet, basename='history')
subaccounts_history_urlpatterns = subaccounts_history_router.urls

subaccount_history_router = routers.SimpleRouter()
subaccount_history_router.register(
    r'', SubAccountHistoryViewSet, basename='history')
subaccount_history_urlpatterns = subaccount_history_router.urls

from rest_framework import routers

from .views import (
    AccountsHistoryViewSet, AccountHistoryViewSet, SubAccountsHistoryViewSet,
    SubAccountHistoryViewSet, ActualsHistoryViewSet, ActualHistoryViewSet)

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

actuals_history_router = routers.SimpleRouter()
actuals_history_router.register(r'', ActualsHistoryViewSet, basename='history')
actuals_history_urlpatterns = actuals_history_router.urls

actual_history_router = routers.SimpleRouter()
actual_history_router.register(r'', ActualHistoryViewSet, basename='history')
actual_history_urlpatterns = actual_history_router.urls

from rest_framework import routers

from .views import AccountsHistoryViewSet, AccountHistoryViewSet

app_name = "history"

accounts_history_router = routers.SimpleRouter()
accounts_history_router.register(
    r'', AccountsHistoryViewSet, basename='history')
accounts_history_urlpatterns = accounts_history_router.urls

account_history_router = routers.SimpleRouter()
account_history_router.register(r'', AccountHistoryViewSet, basename='history')
account_history_urlpatterns = account_history_router.urls

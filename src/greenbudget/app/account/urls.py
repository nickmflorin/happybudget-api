from django.urls import path, include
from rest_framework import routers

from greenbudget.app.actual.urls import account_actuals_urlpatterns
from greenbudget.app.comment.urls import account_comments_urlpatterns
from greenbudget.app.history.urls import (
    accounts_history_urlpatterns, account_history_urlpatterns)
from greenbudget.app.subaccount.urls import account_subaccounts_urlpatterns

from .views import (
    BudgetAccountViewSet,
    AccountViewSet,
    AccountGroupViewSet,
    AccountSubAccountGroupViewSet
)


app_name = "account"

budget_accounts_router = routers.SimpleRouter()
budget_accounts_router.register(r'', BudgetAccountViewSet, basename='account')
budget_accounts_urlpatterns = [
    path('history/', include(accounts_history_urlpatterns)),
] + budget_accounts_router.urls

account_groups_router = routers.SimpleRouter()
account_groups_router.register(
    r'', AccountSubAccountGroupViewSet,
    basename='account-subaccount-group'
)
account_subaccounts_groups_urlpatterns = account_groups_router.urls

router = routers.SimpleRouter()
router.register(r'', AccountViewSet, basename='account')
router.register(
    r'groups',
    AccountGroupViewSet,
    basename='account-group'
)
urlpatterns = router.urls + [
    path('<int:account_pk>/', include([
        path('actuals/', include(account_actuals_urlpatterns)),
        path('comments/', include(account_comments_urlpatterns)),
        path('history/', include(account_history_urlpatterns)),
        path('groups/', include(account_subaccounts_groups_urlpatterns)),
        path('subaccounts/', include(account_subaccounts_urlpatterns)),
    ]))
]

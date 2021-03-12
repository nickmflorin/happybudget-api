from django.urls import path, include
from rest_framework import routers

from greenbudget.app.actual.urls import account_actuals_urlpatterns
from greenbudget.app.comment.urls import account_comments_urlpatterns
from greenbudget.app.subaccount.urls import account_subaccounts_urlpatterns

from .views import BudgetAccountViewSet, AccountViewSet


app_name = "account"

budget_accounts_router = routers.SimpleRouter()
budget_accounts_router.register(r'', BudgetAccountViewSet, basename='account')
budget_accounts_urlpatterns = budget_accounts_router.urls + [
    path('<int:account_pk>/', include([
        path('subaccounts/', include(account_subaccounts_urlpatterns)),
    ]))
]

router = routers.SimpleRouter()
router.register(r'', AccountViewSet, basename='account')
urlpatterns = router.urls + [
    path('<int:account_pk>/', include([
        path('actuals/', include(account_actuals_urlpatterns)),
        path('comments/', include(account_comments_urlpatterns)),
    ]))
]

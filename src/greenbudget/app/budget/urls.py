from django.urls import path, include
from rest_framework import routers

from greenbudget.app.account.urls import budget_accounts_urlpatterns
from greenbudget.app.actual.urls import budget_actuals_router

from .views import (
    UserBudgetViewSet, UserBudgetTrashViewSet, BudgetElementViewSet)


app_name = "budget"

router = routers.SimpleRouter()
router.register(
    r'trash', UserBudgetTrashViewSet, basename='trash')
router.register(r'', UserBudgetViewSet, basename='budget')

urlpatterns = router.urls + [
    path('<int:budget_pk>/', include([
        path('elements/', BudgetElementViewSet.as_view({
            'get': 'list'
        })),
        path('accounts/', include(budget_accounts_urlpatterns)),
        path('actuals/', include(budget_actuals_router)),
    ]))
]

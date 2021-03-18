from django.urls import path, include
from rest_framework import routers

from greenbudget.app.history.urls import (
    actuals_history_urlpatterns, actual_history_urlpatterns)

from .views import (
    ActualsViewSet, AccountActualsViewSet, SubAccountActualsViewSet,
    BudgetActualsViewSet)


app_name = "actual"

account_actuals_router = routers.SimpleRouter()
account_actuals_router.register(
    r'', AccountActualsViewSet, basename='actual')
account_actuals_urlpatterns = account_actuals_router.urls

subaccount_actuals_router = routers.SimpleRouter()
subaccount_actuals_router.register(
    r'', SubAccountActualsViewSet, basename='actual')
subaccount_actuals_urlpatterns = subaccount_actuals_router.urls

budget_actuals_router = routers.SimpleRouter()
budget_actuals_router.register(
    r'', BudgetActualsViewSet, basename='actual')
budget_actuals_urlpatterns = budget_actuals_router.urls + [
    path('history/', include(actuals_history_urlpatterns)),
]

router = routers.SimpleRouter()
router.register(r'', ActualsViewSet, basename='actual')
urlpatterns = router.urls + [
    path('<int:actual_pk>/', include([
        path('history/', include(actual_history_urlpatterns)),
    ]))
]

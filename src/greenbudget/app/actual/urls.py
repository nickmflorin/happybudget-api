from django.urls import path, include
from rest_framework import routers

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
subaccount_actuals_urls = subaccount_actuals_router.urls

budget_actuals_router = routers.SimpleRouter()
budget_actuals_router.register(
    r'', BudgetActualsViewSet, basename='actual')
budget_actuals_router = budget_actuals_router.urls

router = routers.SimpleRouter()
router.register(r'', ActualsViewSet, basename='actual')
urlpatterns = router.urls

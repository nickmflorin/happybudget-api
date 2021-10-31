from django.urls import path, include
from rest_framework_nested import routers

from greenbudget.lib.drf.router import combine_routers

from .views import (
    BudgetViewSet,
    BudgetFringeViewSet,
    BudgetGroupViewSet,
    BudgetMarkupViewSet,
    BudgetActualsViewSet,
    BudgetAccountViewSet,
    BudgetSubAccountViewSet
)

app_name = "budget"

router = routers.SimpleRouter()
router.register(r'', BudgetViewSet, basename='budget')

budget_fringes_router = routers.NestedSimpleRouter(router, r'', lookup='budget')
budget_fringes_router.register(
    r'fringes', BudgetFringeViewSet, basename='budget-fringes')

budget_subaccounts_router = routers.NestedSimpleRouter(
    router, r'', lookup='budget')
budget_subaccounts_router.register(
    r'subaccounts', BudgetSubAccountViewSet, basename='budget-subaccount')

budget_markup_router = routers.NestedSimpleRouter(
    router, r'', lookup='budget')
budget_markup_router.register(
    r'markups', BudgetMarkupViewSet, basename='budget-markup')

budget_groups_router = routers.NestedSimpleRouter(
    router, r'', lookup='budget')
budget_groups_router.register(
    r'groups', BudgetGroupViewSet, basename='budget-group')

budget_actuals_router = routers.NestedSimpleRouter(
    router, r'', lookup='budget')
budget_actuals_router.register(
    r'actuals', BudgetActualsViewSet, basename='budget-actual')

budget_accounts_router = routers.SimpleRouter()
budget_accounts_router.register(
    r'', BudgetAccountViewSet, basename='budget-account')

urlpatterns = combine_routers(
    router,
    budget_fringes_router,
    budget_subaccounts_router,
    budget_groups_router,
    budget_markup_router,
    budget_actuals_router
) + [
    path('<int:budget_pk>/', include([
        path('accounts/', include(budget_accounts_router.urls)),
    ]))
]

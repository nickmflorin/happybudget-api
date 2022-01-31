from django.urls import path, include
from rest_framework_nested import routers

from greenbudget.lib.drf.router import combine_routers

from .views import (
    BudgetViewSet,
    BudgetFringeViewSet,
    BudgetGroupViewSet,
    BudgetMarkupViewSet,
    BudgetActualsViewSet,
    BudgetChildrenViewSet,
    BudgetActualsOwnersViewSet,
    BudgetShareTokenViewSet
)

app_name = "budget"

router = routers.SimpleRouter()
router.register(r'', BudgetViewSet, basename='budget')

budget_fringes_router = routers.NestedSimpleRouter(router, r'', lookup='budget')
budget_fringes_router.register(
    r'fringes', BudgetFringeViewSet, basename='fringe')

budget_actuals_owners_router = routers.NestedSimpleRouter(
    router, r'', lookup='budget')
budget_actuals_owners_router.register(
    r'actual-owners', BudgetActualsOwnersViewSet, basename='actual-owner')

budget_markup_router = routers.NestedSimpleRouter(router, r'', lookup='budget')
budget_markup_router.register(
    r'markups', BudgetMarkupViewSet, basename='markup')

budget_groups_router = routers.NestedSimpleRouter(router, r'', lookup='budget')
budget_groups_router.register(r'groups', BudgetGroupViewSet, basename='group')

budget_actuals_router = routers.NestedSimpleRouter(router, r'', lookup='budget')
budget_actuals_router.register(
    r'actuals', BudgetActualsViewSet, basename='actual')

budget_share_token_router = routers.SimpleRouter()
budget_share_token_router.register(
    r'', BudgetShareTokenViewSet, basename='share-token')

budget_children_router = routers.SimpleRouter()
budget_children_router.register(r'', BudgetChildrenViewSet, basename='child')

urlpatterns = combine_routers(
    router,
    budget_fringes_router,
    budget_actuals_owners_router,
    budget_groups_router,
    budget_markup_router,
    budget_actuals_router,
    budget_share_token_router
) + [
    path('<int:budget_pk>/', include([
        path('children/', include(budget_children_router.urls)),
        path('share-token/', include(budget_share_token_router.urls))
    ]))
]

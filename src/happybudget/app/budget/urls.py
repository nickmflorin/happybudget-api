from django.urls import path, include
from rest_framework import routers

from .views import (
    BudgetViewSet,
    BudgetFringeViewSet,
    BudgetGroupViewSet,
    BudgetMarkupViewSet,
    BudgetActualsViewSet,
    BudgetChildrenViewSet,
    BudgetActualsOwnersViewSet,
    BudgetPublicTokenViewSet,
    BudgetCollaboratorsViewSet,
    CollaboratingBudgetViewSet,
    AcrhivedBudgetViewSet
)

app_name = "budget"

router = routers.SimpleRouter()
router.register(
    r'collaborating',
    CollaboratingBudgetViewSet,
    basename='collaborating-budget'
)
router.register(r'archived', AcrhivedBudgetViewSet, basename='archived-budget')
router.register(r'', BudgetViewSet, basename='budget')

budget_fringes_router = routers.SimpleRouter()
budget_fringes_router.register(r'', BudgetFringeViewSet, basename='fringe')

budget_actuals_owners_router = routers.SimpleRouter()
budget_actuals_owners_router.register(
    r'', BudgetActualsOwnersViewSet, basename='actual-owner')

budget_markup_router = routers.SimpleRouter()
budget_markup_router.register(r'', BudgetMarkupViewSet, basename='markup')

budget_groups_router = routers.SimpleRouter()
budget_groups_router.register(r'', BudgetGroupViewSet, basename='group')

budget_actuals_router = routers.SimpleRouter()
budget_actuals_router.register(r'', BudgetActualsViewSet, basename='actual')

budget_public_token_router = routers.SimpleRouter()
budget_public_token_router.register(
    r'', BudgetPublicTokenViewSet, basename='public-token')

budget_children_router = routers.SimpleRouter()
budget_children_router.register(r'', BudgetChildrenViewSet, basename='child')

budget_collaborators_router = routers.SimpleRouter()
budget_collaborators_router.register(
    r'', BudgetCollaboratorsViewSet, basename='collaborator')

urlpatterns = router.urls + [
    path('<int:pk>/', include([
        path('children/', include(budget_children_router.urls)),
        path('public-token/', include(budget_public_token_router.urls)),
        path('actuals/', include(budget_actuals_router.urls)),
        path('fringes/', include(budget_fringes_router.urls)),
        path('markups/', include(budget_markup_router.urls)),
        path('groups/', include(budget_groups_router.urls)),
        path('collaborators/', include(budget_collaborators_router.urls)),
        path('actual-owners/', include(budget_actuals_owners_router.urls))
    ]))
]

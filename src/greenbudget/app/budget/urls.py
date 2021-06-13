from django.urls import path, include
from rest_framework import routers

from greenbudget.app.comment.urls import budget_comments_urlpatterns
from greenbudget.app.history.urls import (
    actuals_history_urlpatterns, accounts_history_urlpatterns)

from .views import (
    LineItemViewSet,
    BudgetViewSet,
    BudgetTrashViewSet,
    BudgetFringeViewSet,
    BudgetGroupViewSet,
    BudgetActualsViewSet,
    BudgetAccountViewSet,
    LineItemTreeViewSet
)

app_name = "budget"

router = routers.SimpleRouter()
router.register(r'trash', BudgetTrashViewSet, basename='budget-trash')
router.register(r'', BudgetViewSet, basename='budget')

budget_fringes_router = routers.SimpleRouter()
budget_fringes_router.register(
    r'', BudgetFringeViewSet, basename='budget-fringe')

budget_actuals_router = routers.SimpleRouter()
budget_actuals_router.register(
    r'', BudgetActualsViewSet, basename='budget-actual')
budget_actuals_urlpatterns = budget_actuals_router.urls + [
    path('history/', include(actuals_history_urlpatterns)),
]

budget_accounts_router = routers.SimpleRouter()
budget_accounts_router.register(
    r'', BudgetAccountViewSet, basename='budget-account')
budget_accounts_urlpatterns = [
    path('history/', include(accounts_history_urlpatterns)),
] + budget_accounts_router.urls


budget_line_items_router = routers.SimpleRouter()
budget_line_items_router.register(r'', LineItemViewSet, basename='budget-item')
budget_line_items_router.register(
    r'tree', LineItemTreeViewSet, basename='budget-item-tree')

budget_groups_router = routers.SimpleRouter()
budget_groups_router.register(r'', BudgetGroupViewSet, basename='budget-group')

urlpatterns = router.urls + [
    path('<int:budget_pk>/', include([
        path('items/', include(budget_line_items_router.urls)),
        path('accounts/', include(budget_accounts_urlpatterns)),
        path('actuals/', include(budget_actuals_urlpatterns)),
        path('comments/', include(budget_comments_urlpatterns)),
        path('groups/', include(budget_groups_router.urls)),
        path('fringes/', include(budget_fringes_router.urls)),
    ]))
]

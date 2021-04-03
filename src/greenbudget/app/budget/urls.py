from django.urls import path, include
from rest_framework import routers

from greenbudget.app.account.urls import budget_accounts_urlpatterns
from greenbudget.app.actual.urls import budget_actuals_urlpatterns
from greenbudget.app.comment.urls import budget_comments_urlpatterns

from .views import (
    BudgetAccountGroupViewSet,
    BudgetViewSet,
    BudgetTrashViewSet,
    BudgetFringesViewSet,
    FringesViewSet
)


app_name = "budget"

router = routers.SimpleRouter()
router.register(
    r'trash', BudgetTrashViewSet, basename='trash')
router.register(r'fringes', FringesViewSet, basename='fringe')
router.register(r'', BudgetViewSet, basename='budget')

budget_fringes_router = routers.SimpleRouter()
budget_fringes_router.register(r'', BudgetFringesViewSet, basename='fringe')

budget_groups_router = routers.SimpleRouter()
budget_groups_router.register(
    r'', BudgetAccountGroupViewSet,
    basename='budget-account-group'
)
budget_accounts_groups_urlpatterns = budget_groups_router.urls

urlpatterns = router.urls + [
    path('<int:budget_pk>/', include([
        path('items/', include('greenbudget.app.budget_item.urls')),
        path('accounts/', include(budget_accounts_urlpatterns)),
        path('actuals/', include(budget_actuals_urlpatterns)),
        path('comments/', include(budget_comments_urlpatterns)),
        path('groups/', include(budget_accounts_groups_urlpatterns)),
        path('fringes/', include(budget_fringes_router.urls)),
    ]))
]

from django.urls import path, include
from rest_framework import routers

from greenbudget.app.account.urls import budget_accounts_urlpatterns
from greenbudget.app.actual.urls import budget_actuals_urlpatterns
from greenbudget.app.comment.urls import budget_comments_urlpatterns

from .views import UserBudgetViewSet, UserBudgetTrashViewSet


app_name = "budget"

router = routers.SimpleRouter()
router.register(
    r'trash', UserBudgetTrashViewSet, basename='trash')
router.register(r'', UserBudgetViewSet, basename='budget')

urlpatterns = router.urls + [
    path('<int:budget_pk>/', include([
        path('items/', include('greenbudget.app.budget_item.urls')),
        path('accounts/', include(budget_accounts_urlpatterns)),
        path('actuals/', include(budget_actuals_urlpatterns)),
        path('comments/', include(budget_comments_urlpatterns)),
    ]))
]

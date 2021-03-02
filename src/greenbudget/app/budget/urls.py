from rest_framework import routers

from .views import UserBudgetViewSet, UserBudgetTrashViewSet


app_name = "budget"

budget_router = routers.SimpleRouter()
budget_router.register(
    r'trash', UserBudgetTrashViewSet, basename='trash')
budget_router.register(r'', UserBudgetViewSet, basename='budget')

urlpatterns = budget_router.urls

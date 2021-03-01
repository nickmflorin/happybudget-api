from rest_framework import routers

from .views import UserBudgetViewSet


app_name = "budget"

budget_router = routers.SimpleRouter()
budget_router.register(r'', UserBudgetViewSet, basename='budget')

urlpatterns = budget_router.urls

from rest_framework import routers

from .views import BudgetItemViewSet

router = routers.SimpleRouter()
router.register(r'', BudgetItemViewSet, basename='item')
urlpatterns = router.urls

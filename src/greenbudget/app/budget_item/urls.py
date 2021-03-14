from rest_framework import routers

from .views import BudgetItemViewSet, BudgetItemTreeViewSet

router = routers.SimpleRouter()
router.register(r'', BudgetItemViewSet, basename='item')
router.register(r'tree', BudgetItemTreeViewSet, basename='item-tree')
urlpatterns = router.urls

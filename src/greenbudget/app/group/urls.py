from rest_framework import routers

from .views import GroupViewSet

router = routers.SimpleRouter()
router.register(r'', GroupViewSet, basename='group')

urlpatterns = router.urls

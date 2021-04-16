from rest_framework import routers

from .views import FringesViewSet

router = routers.SimpleRouter()
router.register(r'', FringesViewSet, basename='fringe')

urlpatterns = router.urls

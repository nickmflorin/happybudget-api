from rest_framework import routers

from .views import ActualsViewSet, ActualTypeViewSet

app_name = "actual"

router = routers.SimpleRouter()
router.register(r'types', ActualTypeViewSet, basename='actual-type')
router.register(r'', ActualsViewSet, basename='actual')

urlpatterns = router.urls

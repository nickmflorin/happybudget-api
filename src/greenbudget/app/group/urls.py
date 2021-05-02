from rest_framework import routers

from .views import GroupViewSet, GroupColorsViewSet

app_name = 'group'

router = routers.SimpleRouter()
router.register(r'colors', GroupColorsViewSet, basename='group-color')
router.register(r'', GroupViewSet, basename='group')

urlpatterns = router.urls

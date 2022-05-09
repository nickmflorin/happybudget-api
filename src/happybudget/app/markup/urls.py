from rest_framework import routers

from .views import MarkupViewSet

app_name = 'markup'

router = routers.SimpleRouter()
router.register(r'', MarkupViewSet, basename='markup')

urlpatterns = router.urls

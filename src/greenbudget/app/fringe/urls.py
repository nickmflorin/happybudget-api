from rest_framework import routers

from greenbudget.app.tagging.views import ColorsViewSet

from .models import Fringe
from .views import FringesViewSet

router = routers.SimpleRouter()
router.register(r'colors', ColorsViewSet(Fringe), basename='fringe-color')
router.register(r'', FringesViewSet, basename='fringe')

urlpatterns = router.urls

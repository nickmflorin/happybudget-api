from rest_framework import routers

from greenbudget.app.tagging.views import ColorsViewSet

from .models import Group
from .views import GroupViewSet

app_name = 'group'

router = routers.SimpleRouter()
router.register(r'colors', ColorsViewSet(Group), basename='group-color')
router.register(r'', GroupViewSet, basename='group')

urlpatterns = router.urls

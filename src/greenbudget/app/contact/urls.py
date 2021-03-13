from rest_framework import routers

from .views import ContactViewSet

app_name = "contact"

router = routers.SimpleRouter()
router.register(r'', ContactViewSet, basename='contact')
urlpatterns = router.urls

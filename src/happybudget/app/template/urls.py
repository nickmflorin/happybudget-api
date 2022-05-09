from rest_framework import routers

from .views import TemplateCommunityViewSet, TemplateViewSet

app_name = "template"

router = routers.SimpleRouter()
router.register(
    r'community', TemplateCommunityViewSet, basename='community')
router.register(r'', TemplateViewSet, basename='template')

urlpatterns = router.urls

from rest_framework import routers

from .views import HeaderTemplateViewSet

app_name = "pdf"

router = routers.SimpleRouter()
router.register(r'header-templates', HeaderTemplateViewSet,
                basename='header_template')
urlpatterns = router.urls

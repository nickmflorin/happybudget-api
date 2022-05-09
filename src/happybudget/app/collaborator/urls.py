from rest_framework import routers

from .views import CollaboratorViewSet

app_name = "collaborator"

router = routers.SimpleRouter()
router.register(r'', CollaboratorViewSet, basename='collaborator')
urlpatterns = router.urls

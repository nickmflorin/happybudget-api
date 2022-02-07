from django.urls import path, include
from rest_framework import routers

from .views import ActualsViewSet, ActualTypeViewSet, ActualAttachmentViewSet

app_name = "actual"

router = routers.SimpleRouter()
router.register(r'types', ActualTypeViewSet, basename='actual-type')
router.register(r'', ActualsViewSet, basename='actual')

actual_attachments_router = routers.SimpleRouter()
actual_attachments_router.register(
    r'', ActualAttachmentViewSet,
    basename='actual-attachment'
)

urlpatterns = router.urls + [
    path('<int:pk>/', include([
        path('attachments/', include(actual_attachments_router.urls)),
    ]))
]

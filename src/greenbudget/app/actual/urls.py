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
    # We have to use the actual_pk lookup kwarg because we use the PK for
    # the DELETE /actuals/<actual_pk>/attachments/<pk>/ endpoint.
    path('<int:actual_pk>/', include([
        path('attachments/', include(actual_attachments_router.urls)),
    ]))
]

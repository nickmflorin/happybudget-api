from django.urls import path, include
from rest_framework import routers

from .views import ContactViewSet, ContactAttachmentViewSet

app_name = "contact"

router = routers.SimpleRouter()
router.register(r'', ContactViewSet, basename='contact')
urlpatterns = router.urls


contact_attachments_router = routers.SimpleRouter()
contact_attachments_router.register(
    r'', ContactAttachmentViewSet,
    basename='contact-attachment'
)

urlpatterns = router.urls + [
    path('<int:contact_pk>/', include([
        path('attachments/', include(contact_attachments_router.urls)),
    ]))
]

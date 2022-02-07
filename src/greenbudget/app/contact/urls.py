from django.urls import path, include
from rest_framework import routers

from .views import (
    ContactViewSet, ContactAttachmentViewSet, ContactTaggedActualsViewSet)

app_name = "contact"

router = routers.SimpleRouter()
router.register(r'', ContactViewSet, basename='contact')
urlpatterns = router.urls


contact_attachments_router = routers.SimpleRouter()
contact_attachments_router.register(
    r'',
    ContactAttachmentViewSet,
    basename='attachment'
)

contact_tagged_actuals_router = routers.SimpleRouter()
contact_tagged_actuals_router.register(
    r'',
    ContactTaggedActualsViewSet,
    basename='tagged-actual'
)

urlpatterns = router.urls + [
    path('<int:pk>/', include([
        path('attachments/', include(contact_attachments_router.urls)),
        path('tagged-actuals/', include(contact_tagged_actuals_router.urls)),
    ]))
]

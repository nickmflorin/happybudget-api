from django.urls import path, include
from rest_framework import routers

from .views import (
    SubAccountViewSet,
    SubAccountRecursiveViewSet,
    SubAccountGroupViewSet,
    SubAccountMarkupViewSet,
    SubAccountUnitViewSet,
    SubAccountAttachmentViewSet
)

app_name = "subaccount"

subaccount_children_router = routers.SimpleRouter()
subaccount_children_router.register(
    r'', SubAccountRecursiveViewSet, basename='child')

subaccount_groups_router = routers.SimpleRouter()
subaccount_groups_router.register(
    r'',
    SubAccountGroupViewSet,
    basename='group'
)

subaccount_markup_router = routers.SimpleRouter()
subaccount_markup_router.register(
    r'',
    SubAccountMarkupViewSet,
    basename='markup'
)

subaccount_attachments_router = routers.SimpleRouter()
subaccount_attachments_router.register(
    r'',
    SubAccountAttachmentViewSet,
    basename='attachment'
)

router = routers.SimpleRouter()
router.register(r'units', SubAccountUnitViewSet, basename='unit')
router.register(r'', SubAccountViewSet, basename='subaccount')

urlpatterns = router.urls + [
    path('<int:pk>/', include([
        path('children/', include(subaccount_children_router.urls)),
        path('attachments/', include(subaccount_attachments_router.urls)),
        path('groups/', include(subaccount_groups_router.urls)),
        path('markups/', include(subaccount_markup_router.urls)),
    ]))
]

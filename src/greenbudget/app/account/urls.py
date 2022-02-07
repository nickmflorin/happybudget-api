from django.urls import path, include
from rest_framework import routers

from .views import (
    AccountViewSet,
    AccountMarkupViewSet,
    AccountGroupViewSet,
    AccountChildrenViewSet
)

app_name = "account"

account_groups_router = routers.SimpleRouter()
account_groups_router.register(
    r'',
    AccountGroupViewSet,
    basename='group'
)

account_markup_router = routers.SimpleRouter()
account_markup_router.register(
    r'',
    AccountMarkupViewSet,
    basename='markup'
)

account_children_router = routers.SimpleRouter()
account_children_router.register(
    r'', AccountChildrenViewSet, basename='child')

router = routers.SimpleRouter()
router.register(r'', AccountViewSet, basename='account')

urlpatterns = router.urls + [
    path('<int:pk>/', include([
        path('groups/', include(account_groups_router.urls)),
        path('markups/', include(account_markup_router.urls)),
        path('children/', include(account_children_router.urls)),
    ]))
]

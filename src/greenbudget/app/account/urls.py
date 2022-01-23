from django.urls import path, include
from rest_framework import routers

from .views import (
    AccountViewSet,
    AccountMarkupViewSet,
    AccountGroupViewSet,
    AccountSubAccountViewSet
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

account_subaccounts_router = routers.SimpleRouter()
account_subaccounts_router.register(
    r'', AccountSubAccountViewSet, basename='subaccount')

router = routers.SimpleRouter()
router.register(r'', AccountViewSet, basename='account')

urlpatterns = router.urls + [
    path('<int:account_pk>/', include([
        path('groups/', include(account_groups_router.urls)),
        path('markups/', include(account_markup_router.urls)),
        path('subaccounts/', include(account_subaccounts_router.urls)),
    ]))
]

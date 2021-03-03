from django.urls import path, include
from rest_framework import routers

from .views import (
    SubAccountViewSet, AccountSubAccountViewSet, SubAccountRecursiveViewSet)


app_name = "subaccount"

account_subaccounts_router = routers.SimpleRouter()
account_subaccounts_router.register(
    r'', AccountSubAccountViewSet, basename='subaccount')
account_subaccounts_urlpatterns = account_subaccounts_router.urls

subaccount_subaccounts_router = routers.SimpleRouter()
subaccount_subaccounts_router.register(
    r'', SubAccountRecursiveViewSet, basename='subaccount')

router = routers.SimpleRouter()
router.register(r'', SubAccountViewSet, basename='subaccount')
urlpatterns = router.urls + [
    path('<int:subaccount_pk>/', include([
        path('subaccounts/', include(subaccount_subaccounts_router.urls)),
    ]))
]

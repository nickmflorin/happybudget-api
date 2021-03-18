from django.urls import path, include
from rest_framework import routers

from greenbudget.app.actual.urls import subaccount_actuals_urlpatterns
from greenbudget.app.comment.urls import subaccount_comments_urlpatterns
from greenbudget.app.history.urls import (
    subaccounts_history_urlpatterns, subaccount_history_urlpatterns)

from .views import (
    SubAccountViewSet, AccountSubAccountViewSet, SubAccountRecursiveViewSet)


app_name = "subaccount"

account_subaccounts_router = routers.SimpleRouter()
account_subaccounts_router.register(
    r'', AccountSubAccountViewSet, basename='subaccount')
account_subaccounts_urlpatterns = account_subaccounts_router.urls + [
    path('history/', include(subaccounts_history_urlpatterns)),
]

subaccount_subaccounts_router = routers.SimpleRouter()
subaccount_subaccounts_router.register(
    r'', SubAccountRecursiveViewSet, basename='subaccount')

router = routers.SimpleRouter()
router.register(r'', SubAccountViewSet, basename='subaccount')
urlpatterns = router.urls + [
    path('<int:subaccount_pk>/', include([
        path('subaccounts/', include(subaccount_subaccounts_router.urls)),
        path('actuals/', include(subaccount_actuals_urlpatterns)),
        path('comments/', include(subaccount_comments_urlpatterns)),
        path('history/', include(subaccount_history_urlpatterns)),
    ]))
]

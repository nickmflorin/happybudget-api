from django.urls import path, include
from rest_framework import routers

from greenbudget.app.comment.urls import account_comments_urlpatterns
from greenbudget.app.history.urls import (
    account_history_urlpatterns,
    account_subaccounts_history_urlpatterns
)
from .views import (
    AccountViewSet,
    AccountGroupViewSet,
    AccountSubAccountViewSet,
    AccountActualsViewSet
)

app_name = "account"

account_groups_router = routers.SimpleRouter()
account_groups_router.register(
    r'', AccountGroupViewSet,
    basename='account-subaccount-group'
)

account_subaccounts_router = routers.SimpleRouter()
account_subaccounts_router.register(
    r'', AccountSubAccountViewSet, basename='subaccount')
account_subaccounts_urlpatterns = account_subaccounts_router.urls + [
    path('history/', include(account_subaccounts_history_urlpatterns)),
]

account_actuals_router = routers.SimpleRouter()
account_actuals_router.register(
    r'', AccountActualsViewSet, basename='actual')

router = routers.SimpleRouter()
router.register(r'', AccountViewSet, basename='account')

urlpatterns = router.urls + [
    path('<int:account_pk>/', include([
        path('groups/', include(account_groups_router.urls)),
        path('subaccounts/', include(account_subaccounts_urlpatterns)),
        # Note: These three endpoints will not work for an Account that belongs
        # to a template.  Is there a better way to do this to make that
        # distinction more clear in the URLs?
        path('actuals/', include(account_actuals_router.urls)),
        path('comments/', include(account_comments_urlpatterns)),
        path('history/', include(account_history_urlpatterns)),
    ]))
]

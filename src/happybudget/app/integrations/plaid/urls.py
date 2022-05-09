from django.urls import path

from .views import PlaidLinkTokenView


app_name = 'plaid'

urlpatterns = [
    path(
        'link-token/',
        PlaidLinkTokenView.as_view({'post': 'create'}),
        name='link-token'
    )
]

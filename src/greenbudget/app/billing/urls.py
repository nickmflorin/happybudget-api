from django.urls import path

from .views import (
    ProductView, CheckoutSessionViewSet, SyncCheckoutSessionViewSet,
    PortalSessionViewSet, SubscriptionView)


app_name = "billing"


urlpatterns = [
    path('products/', ProductView.as_view(
        {'get': 'list'},
        hidden=lambda settings: not settings.BILLING_ENABLED
    ), name='product'),
    path(
        'subscription/',
        SubscriptionView.as_view(
            {'get': 'retrieve'},
            hidden=lambda settings: not settings.BILLING_ENABLED
        ),
        name='subscription'
    ),
    path(
        'portal-session/',
        PortalSessionViewSet.as_view(
            {'post': 'create'},
            hidden=lambda settings: not settings.BILLING_ENABLED
        ),
        name='portal-session'
    ),
    path(
        'checkout-session/',
        CheckoutSessionViewSet.as_view(
            {'post': 'create'},
            hidden=lambda settings: not settings.BILLING_ENABLED
        ),
        name='checkout-session'
    ),
    path(
        'sync-checkout-session/',
        SyncCheckoutSessionViewSet.as_view(
            {'patch': 'update'},
            hidden=lambda settings: not settings.BILLING_ENABLED
        ),
        name='sync-checkout-session'
    )
]

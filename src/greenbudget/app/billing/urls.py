from django.urls import path

from .views import (
    ProductView, CheckoutSessionViewSet, SyncCheckoutSessionViewSet,
    PortalSessionViewSet, SubscriptionView)


app_name = "billing"


urlpatterns = [
    path('products/', ProductView.as_view({'get': 'list'}), name='product'),
    path(
        'subscription/',
        SubscriptionView.as_view({'get': 'retrieve'}),
        name='subscription'
    ),
    path(
        'portal-session/',
        PortalSessionViewSet.as_view({'post': 'create'}),
        name='portal-session'
    ),
    path(
        'checkout-session/',
        CheckoutSessionViewSet.as_view({'post': 'create'}),
        name='checkout-session'
    ),
    path(
        'sync-checkout-session/',
        SyncCheckoutSessionViewSet.as_view({'patch': 'update'}),
        name='sync-checkout-session'
    )
]

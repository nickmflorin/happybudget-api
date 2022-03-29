from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from rest_framework import routers

from .views import (
    UserRegistrationView, ActiveUserViewSet, ChangePasswordView, UserViewSet)

app_name = "user"

user_router = routers.SimpleRouter()
user_router.register(r'', UserViewSet, basename='user')

urlpatterns = user_router.urls + [
    path('change-password/', csrf_exempt(ChangePasswordView.as_view({
        'patch': 'partial_update',
    }))),
    path('registration/', csrf_exempt(UserRegistrationView.as_view({
        'post': 'create',
    }))),
    path('user/', ActiveUserViewSet.as_view(
        {'patch': 'partial_update'}, basename='user'))
]

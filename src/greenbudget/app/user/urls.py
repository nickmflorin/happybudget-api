from django.views.decorators.csrf import csrf_exempt
from django.urls import path, include

from rest_framework import routers

from .views import (
    UserRegistrationView, ActiveUserViewSet, ChangePasswordView)

app_name = "user"

user_router = routers.SimpleRouter()
user_router.register(r'', ActiveUserViewSet, basename='user')

urlpatterns = [
    path('change-password/', csrf_exempt(ChangePasswordView.as_view({
        'patch': 'partial_update',
    }))),
    path('registration/', csrf_exempt(UserRegistrationView.as_view({
        'post': 'create',
    }))),
    path('user/', include(user_router.urls))
]

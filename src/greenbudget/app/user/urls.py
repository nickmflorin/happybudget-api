from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from .views import (
    UserRegistrationView, ActiveUserViewSet, ChangePasswordView)

app_name = "user"

urlpatterns = [
    path('change-password/', csrf_exempt(ChangePasswordView.as_view({
        'patch': 'partial_update',
    }))),
    path('registration/', csrf_exempt(UserRegistrationView.as_view({
        'post': 'create',
    }))),
    path('user/', ActiveUserViewSet.as_view(
        {'patch': 'partial_update'}, basename='user'))
]

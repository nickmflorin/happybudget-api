from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from .views import (
    UserRegistrationView, ActiveUserViewSet, temp_upload_user_image_view,
    UserEmailVerificationView, SendUserEmailVerificationView)

app_name = "user"

urlpatterns = [
    path('temp_upload_user_image/', temp_upload_user_image_view),
    path('registration/', csrf_exempt(UserRegistrationView.as_view({
        'post': 'create',
    }))),
    path('verify-email/', csrf_exempt(UserEmailVerificationView.as_view({
        'post': 'create',
    }))),
    path('send-verification-email/', csrf_exempt(
        SendUserEmailVerificationView.as_view({'post': 'create'})
    )),
    path('user/', ActiveUserViewSet.as_view({
        'patch': 'partial_update',
    })),
]

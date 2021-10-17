from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from .views import (
    LoginView, LogoutView, ResetPasswordView, ForgotPasswordView,
    SocialLoginView, EmailVerificationView, SendEmailVerificationView,
    TokenRefreshView, TokenValidateView)


app_name = "authentication"


urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('validate/', TokenValidateView.as_view(), name='validate'),
    path('login/', csrf_exempt(LoginView.as_view()), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('reset-password/', ResetPasswordView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('social-login/', csrf_exempt(SocialLoginView.as_view())),
    path('verify-email/', csrf_exempt(EmailVerificationView.as_view())),
    path('send-verification-email/', csrf_exempt(
        SendEmailVerificationView.as_view()
    )),
]

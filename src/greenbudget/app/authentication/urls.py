from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from rest_framework import routers

from .views import (
    LoginView, LogoutView, RecoverPasswordView, SocialLoginView,
    VerifyEmailView, AuthTokenValidateView, PasswordRecoveryTokenValidateView,
    EmailTokenValidateView, PasswordResetTokenValidateView, ShareTokenView,
    ShareTokenValidateView)


app_name = "authentication"


share_token_router = routers.SimpleRouter()
share_token_router.register(
    r'share-tokens', ShareTokenView, basename='share-token')

urlpatterns = [
    path('login/', csrf_exempt(LoginView.as_view()), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('validate/', AuthTokenValidateView.as_view(), name='validate'),
    path(
        'validate-share/',
        ShareTokenValidateView.as_view(),
        name='validate-share'
    ),
    path(
        'validate-password-recovery-token/',
        PasswordRecoveryTokenValidateView.as_view(),
    ),
    path(
        'validate-email-verification-token/',
        EmailTokenValidateView.as_view()
    ),
    path('reset-password/', PasswordResetTokenValidateView.as_view()),
    path('recover-password/', RecoverPasswordView.as_view()),
    path('social-login/', csrf_exempt(SocialLoginView.as_view())),
    path('verify-email/', csrf_exempt(VerifyEmailView.as_view())),
] + share_token_router.urls

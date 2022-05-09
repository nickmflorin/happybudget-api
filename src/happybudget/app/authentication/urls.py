from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from rest_framework import routers

from .views import (
    LoginView, LogoutView, RecoverPasswordView, SocialLoginView,
    VerifyEmailView, AuthTokenValidateView, PasswordRecoveryTokenValidateView,
    EmailTokenValidateView, PasswordResetTokenValidateView, PublicTokenView,
    PublicTokenValidateView)


app_name = "authentication"


public_token_router = routers.SimpleRouter()
public_token_router.register(
    r'public-tokens', PublicTokenView, basename='public-token')


def email_url_hidden(settings):
    return not settings.EMAIL_ENABLED


def email_verification_url_hidden(settings):
    return not settings.EMAIL_ENABLED or not settings.EMAIL_VERIFICATION_ENABLED


def social_url_hidden(settings):
    return not settings.SOCIAL_AUTHENTICATION_ENABLED


urlpatterns = [
    path('login/', csrf_exempt(LoginView.as_view()), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('validate/', AuthTokenValidateView.as_view(), name='validate'),
    path(
        'validate-public/',
        PublicTokenValidateView.as_view(),
        name='validate-public'
    ),
    path(
        'validate-password-recovery-token/',
        PasswordRecoveryTokenValidateView.as_view(),
    ),
    path(
        'validate-email-verification-token/',
        EmailTokenValidateView.as_view(hidden=email_url_hidden)
    ),
    path('reset-password/',
        PasswordResetTokenValidateView.as_view(hidden=email_url_hidden)),
    path('recover-password/',
        RecoverPasswordView.as_view(hidden=email_url_hidden)),
    path('social-login/', csrf_exempt(
        SocialLoginView.as_view(hidden=social_url_hidden))),
    path('verify-email/', csrf_exempt(
        VerifyEmailView.as_view(hidden=email_verification_url_hidden))),
] + public_token_router.urls

from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from .backends import CsrfExcemptCookieSessionAuthentication
from .permissions import IsAnonymous
from .serializers import EmailTokenSerializer, ResetPasswordSerializer
from .tokens import AccessToken
from .views import (
    LoginView, LogoutView, RecoverPasswordView, SocialLoginView,
    VerifyEmailView, TokenRefreshView, TokenValidateView)


app_name = "authentication"


urlpatterns = [
    path('login/', csrf_exempt(LoginView.as_view()), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('validate/', TokenValidateView.as_view(
        force_logout=True,
        authentication_classes=(CsrfExcemptCookieSessionAuthentication, ),
    ), name='validate'),
    path('validate-password-recovery-token/', TokenValidateView.as_view(
        token_location='request',
        permission_classes=(IsAnonymous, ),
        authentication_classes=(),
        token_cls=AccessToken
    )),
    path('validate-email-verification-token/', TokenValidateView.as_view(
        serializer_class=EmailTokenSerializer,
        token_cls=AccessToken,
        token_location='request',
        permission_classes=(IsAnonymous, ),
        authentication_classes=(),
        exclude_permissions=["verified"]
    )),
    path('reset-password/', TokenValidateView.as_view(
        serializer_class=ResetPasswordSerializer,
        token_cls=AccessToken,
        token_location='request',
        permission_classes=(IsAnonymous, ),
        authentication_classes=(),
    )),
    path('recover-password/', RecoverPasswordView.as_view()),
    path('social-login/', csrf_exempt(SocialLoginView.as_view())),
    path('verify-email/', csrf_exempt(VerifyEmailView.as_view())),
]

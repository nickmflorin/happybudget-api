from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import response, status, permissions

from greenbudget.app import views
from greenbudget.app.user.serializers import UserSerializer

from .backends import CsrfExcemptCookieSessionAuthentication
from .middleware import AuthTokenCookieMiddleware
from .permissions import (
    IsAnonymous, IsAuthenticated, IsActive, IsVerified)
from .serializers import (
    LoginSerializer, SocialLoginSerializer, VerifyEmailSerializer,
    AuthTokenValidationSerializer, RecoverPasswordSerializer,
    TokenValidationSerializer, EmailTokenValidationSerializer,
    ResetPasswordTokenValidationSerializer)
from .tokens import AuthToken, AccessToken
from .utils import parse_token_from_request, user_can_authenticate


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


class TokenValidateView(views.GenericView):
    serializer_class = TokenValidationSerializer
    token_user_permission_classes = [IsAuthenticated, IsActive, IsVerified]

    @property
    def token_cls(self):
        raise NotImplementedError()

    @sensitive_post_parameters_m('token')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_serializer(self, request, *args, **kwargs):
        serializer_kwargs = {
            'token_cls': self.token_cls,
            'context': {'request': request},
            'token_user_permission_classes': self.token_user_permission_classes
        }
        # Only include arguments passed to the view into the serializer if
        # they were actually provided.
        serializer_kwargs = dict(
            (k, v) for k, v in serializer_kwargs.items() if v is not None)
        attrs = request.data
        if getattr(self, 'token_location', None) == 'cookies':
            attrs.update(token=parse_token_from_request(request))

        serializer = self.serializer_class(**serializer_kwargs, data=attrs)
        serializer.is_valid(raise_exception=True)
        return serializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(request, *args, **kwargs)
        user = serializer.save()
        return response.Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class AuthTokenValidateView(TokenValidateView):
    token_location = 'cookies'
    authentication_classes = (CsrfExcemptCookieSessionAuthentication, )
    token_cls = AuthToken
    serializer_class = AuthTokenValidationSerializer


class PasswordRecoveryTokenValidateView(TokenValidateView):
    permission_classes = (IsAnonymous, )
    token_cls = AccessToken
    authentication_classes = []


class EmailTokenValidateView(TokenValidateView):
    serializer_class = EmailTokenValidationSerializer
    token_cls = AccessToken
    permission_classes = (IsAnonymous, )
    authentication_classes = []
    token_user_permission_classes = [IsAuthenticated, IsActive]

    def validate_user(self, user):
        return user_can_authenticate(
            user=user,
            permissions=[IsAuthenticated, IsActive]
        )


class PasswordResetTokenValidateView(TokenValidateView):
    serializer_class = ResetPasswordTokenValidationSerializer
    token_cls = AccessToken
    permission_classes = (IsAnonymous, )
    authentication_classes = []

    def validate_user(self, user):
        return user_can_authenticate(
            user=user,
            permissions=[IsAuthenticated, IsActive]
        )


class LogoutView(views.GenericView):
    authentication_classes = []
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        logout(request)
        resp = response.Response(status=status.HTTP_201_CREATED)
        return AuthTokenCookieMiddleware.delete_cookie(resp)


class AbstractUnauthenticatedView(views.GenericView):
    authentication_classes = []
    permission_classes = (IsAnonymous, )

    def get_response_data(self, data):
        return {}

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return response.Response(
            self.get_response_data(data),
            status=status.HTTP_201_CREATED
        )


class AbstractLoginView(AbstractUnauthenticatedView):
    def get_response_data(self, user):
        data = UserSerializer(user).data
        if user.is_first_time is True:
            user.is_first_time = False
            user.save(update_fields=['is_first_time'])
        return data


class SocialLoginView(AbstractLoginView):
    serializer_class = SocialLoginSerializer

    @sensitive_post_parameters_m('token_id')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class LoginView(AbstractLoginView):
    serializer_class = LoginSerializer

    @sensitive_post_parameters_m('password')
    def dispatch(self, request, *args, **kwargs):
        return super(LoginView, self).dispatch(request, *args, **kwargs)


class VerifyEmailView(AbstractUnauthenticatedView):
    serializer_class = VerifyEmailSerializer


class RecoverPasswordView(AbstractUnauthenticatedView):
    serializer_class = RecoverPasswordSerializer

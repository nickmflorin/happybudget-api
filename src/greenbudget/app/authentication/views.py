from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import views, response, generics, status, permissions

from greenbudget.app.user.serializers import UserSerializer

from .backends import CsrfExcemptCookieSessionAuthentication
from .middleware import AuthTokenCookieMiddleware
from .permissions import IsAnonymous, IsAuthenticated, IsVerified, IsApproved
from .serializers import (
    LoginSerializer, SocialLoginSerializer, VerifyEmailSerializer,
    AuthTokenSerializer, RecoverPasswordSerializer)
from .utils import parse_token_from_request


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


class TokenValidateView(views.APIView):
    serializer_class = None
    token_location = 'cookies'
    authentication_classes = (CsrfExcemptCookieSessionAuthentication, )
    force_logout = None
    token_cls = None
    serializer_class = AuthTokenSerializer
    token_user_permission_classes = (IsAuthenticated, IsVerified, IsApproved)

    @sensitive_post_parameters_m('token')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_serializer(self, request, *args, **kwargs):
        serializer_kwargs = {
            'force_logout': self.force_logout,
            'token_cls': self.token_cls,
            'token_user_permission_classes': self.token_user_permission_classes,
            'context': {'request': request}
        }
        # Only include arguments passed to the view into the serializer if
        # they were actually provided.
        serializer_kwargs = dict(
            (k, v) for k, v in serializer_kwargs.items() if v is not None)
        attrs = request.data
        if self.token_location == 'cookies':
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


class LogoutView(views.APIView):
    authentication_classes = []
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        logout(request)
        resp = response.Response(status=status.HTTP_201_CREATED)
        return AuthTokenCookieMiddleware.delete_cookie(resp)


class AbstractUnauthenticatedView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = (IsAnonymous, )

    def get_response_data(self, data):
        return {}

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
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

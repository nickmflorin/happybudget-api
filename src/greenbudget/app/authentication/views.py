from django.conf import settings
from django.contrib.auth import logout, login as django_login
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import views, response, generics, status
from rest_framework.permissions import AllowAny

from greenbudget.app.common.exceptions import RateLimitedError
from .serializers import LoginSerializer


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


class LogoutView(views.APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        logout(request)
        resp = response.Response(status=status.HTTP_201_CREATED)
        resp.delete_cookie(settings.JWT_TOKEN_COOKIE_NAME)
        return resp


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    authentication_classes = []
    permission_classes = (AllowAny, )

    @sensitive_post_parameters_m('password')
    def dispatch(self, request, *args, **kwargs):
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise RateLimitedError()

        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        django_login(
            request, user, backend='django.contrib.auth.backends.ModelBackend')

        return response.Response({
            "detail": _("Successfully logged in."),
        }, status=status.HTTP_201_CREATED)

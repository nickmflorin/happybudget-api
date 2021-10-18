from django.contrib.auth import (
    authenticate, login as django_login, get_user_model)

from rest_framework import serializers, exceptions

from greenbudget.app.user.models import User

from .backends import check_user_permissions
from .exceptions import (
    TokenExpiredError, ExpiredToken, InvalidToken, TokenError,
    EmailDoesNotExist)
from .tokens import SlidingToken, AccessToken
from .utils import validate_password, get_user_from_token


class UserEmailField(serializers.EmailField):
    def run_validation(self, *args, **kwargs):
        email = super().run_validation(*args, **kwargs)
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            raise EmailDoesNotExist(self.source)
        check_user_permissions(user, raise_exception=True)
        return user


class AuthTokenSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)

    def __init__(self, *args, **kwargs):
        default_token_cls = getattr(self, 'token_cls', SlidingToken)
        self.token_cls = kwargs.pop('token_cls', default_token_cls)

        default_force_logout = getattr(self, 'force_logout', None)
        self.force_logout = kwargs.pop('force_logout', default_force_logout)

        default_exclude_permissions = getattr(self, 'exclude_permissions', [])
        self.exclude_permissions = kwargs.pop(
            'exclude_permissions', default_exclude_permissions)
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        try:
            user, token_obj = get_user_from_token(
                token=attrs.get('token', None),
                token_cls=self.token_cls,
                strict=True
            )
        except TokenExpiredError as e:
            raise ExpiredToken(
                *e.args,
                user_id=getattr(e, 'user_id', None),
                force_logout=self.force_logout
            ) from e
        except TokenError as e:
            raise InvalidToken(
                *e.args,
                user_id=getattr(e, 'user_id', None),
                force_logout=self.force_logout
            ) from e
        check_user_permissions(
            user=user,
            exclude_permissions=self.exclude_permissions,
            raise_exception=True,
            force_logout=self.force_logout
        )
        return {"user": user, "token": token_obj}

    def create(self, validated_data):
        return validated_data["user"]


class EmailTokenSerializer(AuthTokenSerializer):
    token_cls = AccessToken
    exclude_permissions = ['verified']

    def validate(self, attrs):
        data = super().validate(attrs)
        if data["user"].is_verified:
            raise exceptions.ValidationError("User is already verified.")
        return data

    def create(self, validated_data):
        user = super().create(validated_data)
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        return user


class AbstractLoginSerializer(serializers.Serializer):
    def validate(self, attrs):
        user = authenticate(self.context['request'], **attrs)
        return {"user": user}

    def create(self, validated_data):
        django_login(self.context['request'], validated_data['user'])
        return validated_data['user']


class SocialLoginSerializer(AbstractLoginSerializer):
    token_id = serializers.CharField()
    provider = serializers.ChoiceField(choices=["google"])


class LoginSerializer(AbstractLoginSerializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'})


class ForgotPasswordSerializer(serializers.Serializer):
    email = UserEmailField(required=True, allow_blank=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        return {"user": attrs['email']}

    def create(self, validated_data):
        # Here is where we will send the user password recovery email.
        return validated_data["user"]


class SendEmailVerificationSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True, is_verified=False),
        required=True,
        allow_null=False
    )

    def create(self, validated_data):
        # Here is where we will send the user verification email.
        return validated_data['user']


class ResetPasswordSerializer(AuthTokenSerializer):
    password = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        validators=[validate_password]
    )

    def create(self, validated_data):
        validated_data["user"].set_password(validated_data["password"])
        validated_data["user"].save(update_fields=["password"])
        return validated_data["user"]

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone

from rest_framework_simplejwt.serializers import TokenRefreshSlidingSerializer

from rest_framework import serializers, exceptions

from greenbudget.lib.drf.exceptions import InvalidFieldError
from greenbudget.app.user.models import User

from .backends import check_user_permissions
from .exceptions import (
    TokenExpiredError, ExpiredToken, InvalidToken, TokenError)
from .models import ResetUID
from .tokens import AuthSlidingToken, EmailVerificationSlidingToken
from .utils import validate_password, get_user_from_token


class TokenRefreshSerializer(TokenRefreshSlidingSerializer):

    def __init__(self, *args, **kwargs):
        default_token_cls = getattr(self, 'token_cls', AuthSlidingToken)
        self.token_cls = kwargs.pop('token_cls', default_token_cls)

        self.force_logout = kwargs.pop('force_logout', None)

        default_exclude_permissions = getattr(self, 'exclude_permissions', [])
        self.exclude_permissions = kwargs.pop(
            'exclude_permissions', default_exclude_permissions)
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        try:
            user, token_obj = get_user_from_token(
                token=attrs['token'],
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
        return user, token_obj


class EmailTokenRefreshSerializer(TokenRefreshSerializer):
    token_cls = EmailVerificationSlidingToken
    exclude_permissions = ['verified']


class SocialLoginSerializer(serializers.Serializer):
    token_id = serializers.CharField()
    provider = serializers.ChoiceField(choices=["google"])

    def validate(self, attrs):
        user = authenticate(self.context['request'], **attrs)
        return {"user": user}


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        user = authenticate(self.context['request'], **attrs)
        return {"user": user}


class EmailVerificationSerializer(EmailTokenRefreshSerializer):
    def validate(self, attrs):
        user, _ = super().validate(attrs)
        if user.is_verified:
            raise exceptions.ValidationError("User is already verified.")
        return {"user": user}

    def create(self, validated_data):
        validated_data["user"].is_verified = True
        validated_data["user"].save()
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


class ResetPasswordSerializer(serializers.ModelSerializer):
    token = serializers.SlugRelatedField(
        queryset=ResetUID.objects.all(),
        slug_field='token',
        required=True,
        allow_null=False
    )
    password = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    confirm = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )

    class Meta:
        model = ResetUID
        fields = ('token', 'password', 'confirm')

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_token(self, token):
        expiry_time = timezone.now() - timedelta(
            minutes=60 * settings.PWD_RESET_LINK_EXPIRY_TIME_IN_HRS)
        if not timezone.is_aware(expiry_time):
            expiry_time = timezone.make_aware(expiry_time)

        if token.used:
            raise exceptions.ValidationError("Token was already used.")
        if token.created_at < expiry_time:
            raise exceptions.ValidationError("Token has expired.")
        check_user_permissions(token.user, raise_exception=True)
        return token

    def create(self, validated_data):
        validated_data['token'].used = True
        validated_data['token'].save(update_fields=['used'])
        validated_data['token'].user.set_password(validated_data["password"])
        validated_data['token'].user.save(update_fields=['password'])
        return validated_data['token'].user

    def validate(self, attrs):
        if attrs["confirm"] != attrs["password"]:
            raise InvalidFieldError("confirm",
                message="The passwords do not match.")
        return attrs

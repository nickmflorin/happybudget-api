from django.contrib.auth import (
    authenticate, login as django_login, get_user_model)

from rest_framework import serializers, exceptions

from greenbudget.app.user.models import User

from .exceptions import (
    TokenExpiredError, ExpiredToken, InvalidToken, TokenError,
    EmailDoesNotExist)
from .mail import send_email_verification_email, send_password_recovery_email
from .permissions import IsAuthenticated, IsVerified
from .tokens import SlidingToken, AccessToken
from .utils import validate_password, get_user_from_token


class AuthTokenSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)

    def __init__(self, *args, **kwargs):
        self.check_permissions = kwargs.pop('check_permissions', None)
        default_token_cls = getattr(self, 'token_cls', SlidingToken)
        self.token_cls = kwargs.pop('token_cls', default_token_cls)

        default_force_logout = getattr(self, 'force_logout', None)
        self.force_logout = kwargs.pop('force_logout', default_force_logout)

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
        if self.check_permissions is not None:
            self.check_permissions(user, force_logout=self.force_logout)
        return {"user": user, "token": token_obj}

    def create(self, validated_data):
        return validated_data["user"]


class EmailTokenSerializer(AuthTokenSerializer):
    token_cls = AccessToken

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


class RecoverPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)

    def validate(self, attrs):
        email = attrs['email']
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            raise EmailDoesNotExist('email')
        permissions = [IsAuthenticated(), IsVerified()]
        [p.user_has_permission(user) for p in permissions]
        return {"user": user}

    def create(self, validated_data):
        token = AccessToken.for_user(validated_data["user"])
        send_password_recovery_email(validated_data["user"], str(token))
        return validated_data["user"]


class VerifyEmailSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True, is_verified=False),
        required=True,
        allow_null=False
    )

    def create(self, validated_data):
        token = AccessToken.for_user(validated_data["user"])
        send_email_verification_email(validated_data["user"], str(token))
        return validated_data['user']


class ResetPasswordSerializer(AuthTokenSerializer):
    password = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        validators=[validate_password]
    )

    def validate(self, attrs):
        data = super().validate(attrs)
        return {"user": data["user"], "password": attrs["password"]}

    def create(self, validated_data):
        validated_data["user"].set_password(validated_data["password"])
        validated_data["user"].save(update_fields=["password"])
        return validated_data["user"]

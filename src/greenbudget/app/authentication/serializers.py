from django.contrib.auth import (
    authenticate, login as django_login, get_user_model)

from rest_framework import serializers, exceptions

from greenbudget.app.user.mail import (
    send_email_confirmation_email,
    send_password_recovery_email
)
from greenbudget.app.user.models import User

from .exceptions import EmailDoesNotExist
from .tokens import AuthToken, AccessToken
from .utils import validate_password, parse_token, user_can_authenticate


class TokenValidationSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)

    def __init__(self, *args, **kwargs):
        default_token_cls = getattr(self, 'token_cls', AuthToken)
        self.token_cls = kwargs.pop('token_cls', default_token_cls)
        self.token_user_permission_classes = kwargs.pop(
            'token_user_permission_classes')
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        user, token_obj = parse_token(
            token=attrs.pop('token', None),
            token_cls=self.token_cls
        )
        user = user_can_authenticate(
            user=user,
            permissions=self.token_user_permission_classes,
        )
        attrs.update(user=user, token=token_obj)
        return attrs

    def create(self, validated_data):
        return validated_data["user"]


class AuthTokenValidationSerializer(TokenValidationSerializer):
    token_cls = AuthToken
    force_reload_from_stripe = serializers.BooleanField(default=False)

    def create(self, validated_data):
        user = super().create(validated_data)
        user = user_can_authenticate(
            user=user,
            permissions=self.token_user_permission_classes,
        )
        # If the request indicates to force reload the data from Stripe, we
        # clear the cache so that when the properties are accessed by the
        # UserSerializer, they are reloaded from Stripe's API.
        if validated_data['force_reload_from_stripe']:
            user.flush_stripe_cache()
        # If the request did not indicate to force reload the data from Stripe,
        # we want to update any values that are not already cached with values
        # cached in the JWT token.
        else:
            user.cache_stripe_from_token(validated_data['token'])
        return user


class EmailTokenValidationSerializer(TokenValidationSerializer):
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
        return {"user": user_can_authenticate(user)}

    def create(self, validated_data):
        send_password_recovery_email(validated_data["user"])
        return validated_data["user"]


class VerifyEmailSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True, is_verified=False),
        required=True,
        allow_null=False
    )

    def create(self, validated_data):
        send_email_confirmation_email(validated_data["user"])
        return validated_data['user']


class ResetPasswordTokenValidationSerializer(TokenValidationSerializer):
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

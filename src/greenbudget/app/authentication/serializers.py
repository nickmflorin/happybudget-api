from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone

from rest_framework import serializers

from greenbudget.lib.drf.exceptions import InvalidFieldError

from greenbudget.app.user.models import User

from .exceptions import (
    AccountDisabledError, EmailNotVerified, InvalidCredentialsError,
    EmailDoesNotExist, PasswordResetLinkUsedError, InvalidResetToken,
    PasswordResetLinkExpiredError)
from .models import ResetUID
from .utils import validate_password


class AbstractLoginSerializer(serializers.Serializer):

    def validate(self, user):
        if not user.is_active:
            raise AccountDisabledError()
        elif not user.is_verified:
            raise EmailNotVerified()
        return {'user': user}


class SocialLoginSerializer(AbstractLoginSerializer):
    token_id = serializers.CharField()
    provider = serializers.ChoiceField(choices=["google"])

    def validate(self, attrs):
        user = User.objects.get_or_create_from_social_token(
            token=attrs['token_id'],
            provider=attrs['provider']
        )
        return super().validate(user)


class LoginSerializer(AbstractLoginSerializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'})

    def validate_email(self, email):
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise EmailDoesNotExist()
        return email

    def validate(self, attrs):
        user = authenticate(self.context['request'], **attrs)
        if user is None:
            raise InvalidCredentialsError()
        return super().validate(user)


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        allow_blank=False,
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

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            reset_uid = ResetUID.objects.get(token=attrs["token"])
        except ResetUID.DoesNotExist:
            raise InvalidResetToken()
        else:
            if attrs["confirm"] != attrs["password"]:
                raise InvalidFieldError("confirm",
                    message="The passwords do not match.")
            elif reset_uid.used:
                raise PasswordResetLinkUsedError()
            elif not reset_uid.user.is_active:
                raise AccountDisabledError()
            else:
                expiry_time = timezone.now() - timedelta(
                    minutes=60 * settings.PWD_RESET_LINK_EXPIRY_TIME_IN_HRS)
                if not timezone.is_aware(expiry_time):
                    expiry_time = timezone.make_aware(expiry_time)

                if reset_uid.created_at < expiry_time:
                    raise PasswordResetLinkExpiredError()

                reset_uid.used = True
                reset_uid.save()

                return {
                    "user": reset_uid.user,
                    "password": attrs["password"]
                }

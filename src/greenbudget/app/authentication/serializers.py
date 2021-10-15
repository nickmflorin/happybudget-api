from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone

from rest_framework import serializers, exceptions

from greenbudget.lib.drf.exceptions import InvalidFieldError

from .auth_backends import validate_if_user_can_log_in
from .models import ResetUID
from .utils import validate_password


class SocialLoginSerializer(serializers.Serializer):
    token_id = serializers.CharField()
    provider = serializers.ChoiceField(choices=["google"])

    def validate(self, attrs):
        return authenticate(self.context['request'], **attrs)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        return authenticate(self.context['request'], **attrs)


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
        validate_if_user_can_log_in(token.user)
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

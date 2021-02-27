from django.contrib.auth import authenticate

from rest_framework import serializers

from greenbudget.app.user.models import User

from .exceptions import (
    AccountDisabledError, InvalidCredentialsError, EmailDoesNotExist)


class LoginSerializer(serializers.Serializer):
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
        elif not user.is_active:
            raise AccountDisabledError()
        return {'user': user}

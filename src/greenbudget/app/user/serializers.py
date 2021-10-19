from rest_framework import serializers, validators

from greenbudget.lib.drf.fields import Base64ImageField
from greenbudget.lib.drf.serializers import (
    ModelSerializer)

from greenbudget.app.authentication.utils import validate_password

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    last_name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        allow_null=False,
        validators=[
            validators.UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'password')

    def validate_password(self, value):
        validate_password(value)
        return value


class SimpleUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    profile_image = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'full_name', 'email',
            'profile_image')


class UserSerializer(ModelSerializer):
    first_name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    last_name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        allow_null=False,
        validators=[
            validators.UniqueValidator(queryset=User.objects.all())]
    )
    is_active = serializers.BooleanField(default=True, read_only=True)
    is_admin = serializers.BooleanField(default=False, read_only=True)
    is_staff = serializers.BooleanField(default=False, read_only=True)
    is_superuser = serializers.BooleanField(default=False, read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    timezone = serializers.CharField()
    profile_image = Base64ImageField(required=False, allow_null=True)
    is_first_time = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        nested_fields = ('id', 'first_name', 'last_name', 'email',
            'is_active', 'is_admin', 'is_superuser', 'is_staff', 'full_name',
            'profile_image')
        fields = nested_fields + (
            'created_at', 'updated_at', 'last_login', 'date_joined', 'timezone',
            'is_first_time')

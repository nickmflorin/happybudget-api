
from django.contrib.auth import authenticate
from rest_framework import serializers, exceptions, validators

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from .models import User


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        required=True, allow_null=False, allow_blank=False)
    current = serializers.CharField(
        required=True, allow_null=False, allow_blank=False)

    class Meta:
        model = User
        fields = ('password', 'current')

    def validate_current(self, current):
        auth = authenticate(
            username=self.instance.get_username(),
            password=current
        )
        if not auth:
            raise exceptions.ValidationError("Invalid current password.")
        return current

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


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

    def validate(self, attrs):
        attrs.update(
            is_admin=False,
            is_staff=False,
            is_superuser=False,
            is_active=True,
            username=attrs['email']
        )
        return attrs


class SimpleUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'full_name', 'email')


class UserSerializer(EnhancedModelSerializer):
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
    username = serializers.EmailField(read_only=True)
    is_active = serializers.BooleanField(default=True, read_only=True)
    is_admin = serializers.BooleanField(default=False, read_only=True)
    is_staff = serializers.BooleanField(default=False, read_only=True)
    is_superuser = serializers.BooleanField(default=False, read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    timezone = serializers.SerializerMethodField(read_only=True)
    profile_image = serializers.ImageField(
        required=False,
        allow_empty_file=False
    )

    class Meta:
        model = User
        nested_fields = ('id', 'first_name', 'last_name', 'email', 'username',
            'is_active', 'is_admin', 'is_superuser', 'is_staff', 'full_name')
        fields = nested_fields + (
            'created_at', 'updated_at', 'last_login', 'date_joined', 'timezone',
            'profile_image')

    def get_timezone(self, instance):
        return str(instance.timezone)

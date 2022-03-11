from rest_framework import serializers, validators

from greenbudget.app.authentication.exceptions import InvalidCredentialsError
from greenbudget.app.authentication.utils import validate_password
from greenbudget.app.io.fields import Base64ImageField

from .fields import EmailField
from .models import User


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('password', 'new_password')

    def validate(self, attrs):
        request = self.context['request']
        if not request.user.check_password(attrs['password']):
            raise InvalidCredentialsError(field='password')
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
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
    email = EmailField(
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
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')


class SimpleUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = EmailField(read_only=True)
    profile_image = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'full_name', 'email',
            'profile_image')


class UserSerializer(serializers.ModelSerializer):
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
    email = EmailField(
        required=True,
        allow_blank=False,
        allow_null=False,
        validators=[
            validators.UniqueValidator(queryset=User.objects.all())]
    )
    num_budgets = serializers.IntegerField(read_only=True)
    company = serializers.CharField(allow_null=True, required=False)
    position = serializers.CharField(allow_null=True, required=False)
    address = serializers.CharField(allow_null=True, required=False)
    phone_number = serializers.IntegerField(allow_null=True, required=False)
    is_active = serializers.BooleanField(default=True, read_only=True)
    is_staff = serializers.BooleanField(default=False, read_only=True)
    is_superuser = serializers.BooleanField(default=False, read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    timezone = serializers.CharField()
    profile_image = Base64ImageField(required=False, allow_null=True)
    is_first_time = serializers.BooleanField(read_only=True)
    product_id = serializers.CharField(read_only=True)
    billing_status = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email',
            'is_active', 'is_superuser', 'is_staff', 'full_name',
            'profile_image', 'last_login', 'date_joined', 'timezone',
            'is_first_time', 'company', 'position', 'address', 'phone_number',
            'product_id', 'billing_status', 'num_budgets')

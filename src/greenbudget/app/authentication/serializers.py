import datetime

from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers, exceptions

from greenbudget.lib.drf.exceptions import InvalidFieldError
from greenbudget.lib.drf.validators import UniqueTogetherValidator
from greenbudget.app.user.mail import (
    send_email_confirmation_email,
    send_password_recovery_email
)
from greenbudget.app.budget.models import Budget
from greenbudget.app.user.fields import EmailField
from greenbudget.app.user.models import User

from .exceptions import EmailDoesNotExist
from .fields import ShareTokenInstanceField
from .models import ShareToken
from .tokens import AuthToken, AccessToken
from .utils import (
    validate_password, parse_token, user_can_authenticate, parse_share_token)


class ShareTokenSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    public_id = serializers.UUIDField(required=False, allow_null=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ShareToken
        fields = ('id', 'created_at', 'public_id', 'expires_at', 'is_expired')

    def validate_expires_at(self, value):
        tz = self.context['user'].timezone or datetime.timezone.utc
        if value <= datetime.datetime.now().replace(tzinfo=tz):
            raise exceptions.ValidationError("Value must be in the future.")
        return value

    def validate(self, attrs):
        if 'public_id' in attrs and self.context['request'].method != 'POST':
            raise InvalidFieldError(
                'public_id', message='This field cannot be updated.')
        return attrs

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # If the token is now expired, delete it - but still return the instance
        # so the response is the serialized instance that was deleted.
        if instance.is_expired:
            instance.delete()
        return instance

    def create(self, validated_data, already_attempted=False):
        validator = UniqueTogetherValidator(
            queryset=ShareToken.objects.all(),
            model_fields=('object_id', 'content_type_id'),
            message="Share token already exists for instance."
        )
        try:
            validator(validated_data, self)
        except exceptions.ValidationError as e:
            # Raise the exception if we already attempted the removal of the
            # instance violating the unique constraint, otherwise, we can end
            # up with an infinite recursion.
            if 'unique' in [d.code for d in e.detail] or already_attempted:
                raise e
            # Since the unique validator did not fail, this instance should
            # exist.  In the future we may need to be concerned with race
            # conditions, in which case we should catch ShareToken.DoesNotExist.
            violating_instance = ShareToken.objects.get(
                object_id=self.context['instance'].pk,
                content_type_id=ContentType.objects.get_for_model(
                    type(self.context['instance'])),
            )
            # If the instance that is causing the unique validation error is
            # still active, we want to persist the error.
            if not violating_instance.is_expired:
                raise e
            # The instance causing the unique constraint error is expired, so
            # we can just delete it.  Note that this logic will not be hit as
            # often when we have an async server running for background tasks
            # that can delete expired share tokens.
            violating_instance.delete()
            # Just in case the unique constraint fails again, we want to make
            # the recursion exit to avoid infinite recursions.
            return self.create(validated_data, already_attempted=True)
        else:
            return super().create(validated_data)


class ShareTokenValidationSerializer(serializers.Serializer):
    instance = ShareTokenInstanceField(
        required=True,
        allow_null=False,
        model_classes={'budget': Budget}
    )
    # Do not enforce that this is a UUID field because we want to be able to
    # return authenticated related exceptions if any valid string fails.
    token = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False
    )

    def validate(self, attrs):
        token = parse_share_token(
            token=attrs['token'],
            instance=attrs['instance'],
            public=True
        )
        return {'token': token}

    def create(self, validated_data):
        return validated_data["token"]


class TokenValidationSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

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
        login(self.context['request'], validated_data['user'])
        return validated_data['user']


class SocialLoginSerializer(AbstractLoginSerializer):
    token_id = serializers.CharField()
    provider = serializers.ChoiceField(choices=["google"])


class LoginSerializer(AbstractLoginSerializer):
    email = EmailField(required=True, allow_blank=False)
    password = serializers.CharField(style={'input_type': 'password'})


class RecoverPasswordSerializer(serializers.Serializer):
    email = EmailField(required=True, allow_blank=False)

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

from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)
from greenbudget.app.common.serializers import AncestorSerializer
from greenbudget.app.user.models import User
from greenbudget.app.user.serializers import UserSerializer

from .models import Account


class AccountSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    account_number = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    created_by = UserSerializer(nested=True, read_only=True)
    updated_by = UserSerializer(nested=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    access = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.active(),
        required=False
    )
    budget = serializers.PrimaryKeyRelatedField(read_only=True)
    ancestors = AncestorSerializer(many=True, read_only=True)

    class Meta:
        model = Account
        fields = (
            'id', 'account_number', 'description', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'access', 'budget', 'ancestors')

from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)
from greenbudget.app.account.models import Account
from greenbudget.app.user.serializers import UserSerializer

from .models import SubAccount


class SubAccountSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    line = serializers.CharField(
        required=True,
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
    quantity = serializers.IntegerField(
        required=False,
        allow_null=False
    )
    rate = serializers.DecimalField(
        required=False,
        allow_null=False,
        decimal_places=2,
        max_digits=10
    )
    multiplier = serializers.DecimalField(
        required=False,
        allow_null=False,
        decimal_places=2,
        max_digits=10
    )
    unit = serializers.ChoiceField(choices=SubAccount.UNITS)
    unit_name = serializers.CharField(read_only=True)
    account = serializers.IntegerField(read_only=True, source='account.pk')
    parent = serializers.IntegerField(source='object_id')
    parent_type = serializers.SerializerMethodField()

    class Meta:
        model = SubAccount
        fields = (
            'id', 'name', 'line', 'description', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'quantity', 'rate', 'multiplier',
            'unit', 'unit_name', 'account', 'parent', 'parent_type')

    def get_parent_type(self, instance):
        if isinstance(instance.content_object, Account):
            return "account"
        assert isinstance(instance.content_object, SubAccount)
        return "subaccount"

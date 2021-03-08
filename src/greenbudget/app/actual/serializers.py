from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)
from greenbudget.app.account.models import Account
from greenbudget.app.user.serializers import UserSerializer

from .models import Actual


class ActualSerializer(EnhancedModelSerializer):
    vendor = serializers.CharField(
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
    purchase_order = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    date = serializers.DateTimeField(
        required=False,
        allow_null=False
    )
    payment_id = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    value = serializers.DecimalField(
        required=False,
        allow_null=False,
        decimal_places=2,
        max_digits=10
    )
    payment_method = serializers.ChoiceField(
        required=False,
        choices=Actual.PAYMENT_METHODS
    )
    payment_method_name = serializers.CharField(read_only=True)
    parent = serializers.IntegerField(read_only=True, source='object_id')
    parent_type = serializers.SerializerMethodField()

    class Meta:
        model = Actual
        fields = (
            'id', 'description', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'purchase_order', 'date', 'payment_id', 'value',
            'payment_method', 'payment_method_name', 'parent', 'parent_type',
            'vendor')

    def get_parent_type(self, instance):
        from greenbudget.app.subaccount.models import SubAccount
        if isinstance(instance.parent, Account):
            return "account"
        assert isinstance(instance.parent, SubAccount)
        return "subaccount"
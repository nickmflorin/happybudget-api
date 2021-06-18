from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.fields import ModelChoiceField
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.budget.fields import BudgetFilteredQuerysetPKField
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.serializers import SubAccountSimpleSerializer

from .models import Actual


class ActualSerializer(EnhancedModelSerializer):
    vendor = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True
    )
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    purchase_order = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True
    )
    date = serializers.DateTimeField(
        required=False,
        allow_null=True
    )
    payment_id = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True
    )
    value = serializers.FloatField(required=False, allow_null=True)
    payment_method = ModelChoiceField(
        required=False,
        choices=Actual.PAYMENT_METHODS,
        allow_null=True
    )
    subaccount = BudgetFilteredQuerysetPKField(
        queryset=BudgetSubAccount.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Actual
        fields = (
            'id', 'description', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'purchase_order', 'date', 'payment_id', 'value',
            'payment_method', 'vendor', 'subaccount')
        response = {
            'subaccount': SubAccountSimpleSerializer
        }

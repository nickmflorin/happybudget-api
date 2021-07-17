from rest_framework import serializers

from greenbudget.lib.drf.fields import ModelChoiceField
from greenbudget.lib.drf.serializers import (
    ModelSerializer)

from greenbudget.app.budget.fields import BudgetFilteredQuerysetPKField
from greenbudget.app.contact.models import Contact
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.serializers import SubAccountSimpleSerializer
from greenbudget.app.user.fields import UserFilteredQuerysetPKField

from .models import Actual


class ActualSerializer(ModelSerializer):
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
    contact = UserFilteredQuerysetPKField(
        required=False,
        allow_null=True,
        queryset=Contact.objects.all(),
        user_field='user'
    )

    class Meta:
        model = Actual
        fields = (
            'id', 'description', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'purchase_order', 'date', 'payment_id', 'value',
            'payment_method', 'contact', 'subaccount')
        response = {
            'subaccount': SubAccountSimpleSerializer
        }

from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)
from greenbudget.app.common.serializers import AncestorSerializer
from greenbudget.app.subaccount.serializers import SubAccountSimpleSerializer
from greenbudget.app.user.models import User
from greenbudget.app.user.serializers import UserSerializer

from .models import Account


class AccountSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    identifier = serializers.CharField(
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
    access = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.active(),
        required=False
    )
    budget = serializers.PrimaryKeyRelatedField(read_only=True)
    ancestors = AncestorSerializer(many=True, read_only=True)
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    subaccounts = SubAccountSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = Account
        fields = (
            'id', 'identifier', 'description', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'access', 'budget', 'ancestors',
            'estimated', 'subaccounts', 'actual', 'variance', 'type')

    def validate_identifier(self, value):
        # In the case of creating an Account via a POST request, the budget
        # will be in the context.  In the case of updating an Account via a
        # PATCH request, the instance will be non-null.
        budget = self.context.get('budget')
        if budget is None:
            budget = self.instance.budget
        validator = serializers.UniqueTogetherValidator(
            queryset=Account.objects.filter(budget=budget),
            fields=('identifier', ),
        )
        validator({'identifier': value, 'budget': budget}, self)
        return value

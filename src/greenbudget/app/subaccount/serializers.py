from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)
from greenbudget.app.account.models import Account
from greenbudget.app.common.serializers import AncestorSerializer
from greenbudget.app.user.serializers import UserSerializer

from .models import SubAccount


class SubAccountSimpleSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )

    class Meta:
        model = SubAccount
        fields = ('id', 'name')


class SubAccountSerializer(SubAccountSimpleSerializer):
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    name = serializers.CharField(
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
    unit = serializers.ChoiceField(
        required=False,
        choices=SubAccount.UNITS
    )
    unit_name = serializers.CharField(read_only=True)
    estimated = serializers.DecimalField(
        read_only=True,
        decimal_places=2,
        max_digits=10
    )
    actual = serializers.DecimalField(
        read_only=True,
        decimal_places=2,
        max_digits=10
    )
    variance = serializers.DecimalField(
        read_only=True,
        decimal_places=2,
        max_digits=10
    )
    ancestors = AncestorSerializer(many=True, read_only=True)
    account = serializers.IntegerField(read_only=True, source='account.pk')
    parent = serializers.IntegerField(read_only=True, source='object_id')
    parent_type = serializers.SerializerMethodField()
    subaccounts = SubAccountSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + (
            'identifier', 'name', 'description', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'quantity', 'rate', 'multiplier',
            'unit', 'unit_name', 'account', 'parent', 'parent_type',
            'ancestors', 'estimated', 'subaccounts', 'actual', 'variance')

    def get_parent_type(self, instance):
        if isinstance(instance.parent, Account):
            return "account"
        assert isinstance(instance.parent, SubAccount)
        return "subaccount"

    def validate_identifier(self, value):
        budget = self.context.get('budget')
        if budget is None:
            budget = self.instance.budget
        validator = serializers.UniqueTogetherValidator(
            queryset=budget.items.all(),
            fields=('identifier', ),
        )
        validator({'identifier': value}, self)
        return value

    def validate(self, attrs):
        if self.instance is not None and self.instance.subaccounts.count() != 0:
            if any([field in attrs for field in self.instance.DERIVING_FIELDS]):
                raise exceptions.ValidationError(
                    "Field can only be updated when the sub account is not "
                    "derived."
                )
        return super().validate(attrs)

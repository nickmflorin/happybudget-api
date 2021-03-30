from rest_framework import serializers, exceptions

from greenbudget.app.budget_item.serializers import (
    BudgetItemGroupSerializer, BudgetItemSimpleSerializer)
from greenbudget.app.common.serializers import AncestorSerializer
from greenbudget.app.user.serializers import UserSerializer

from .models import SubAccount, SubAccountGroup


class SubAccountSimpleSerializer(BudgetItemSimpleSerializer):
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )

    class Meta:
        model = SubAccount
        fields = BudgetItemSimpleSerializer.Meta.fields + ('name',)


class SubAccountGroupSerializer(BudgetItemGroupSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=SubAccount.objects.all()
    )

    class Meta:
        model = SubAccountGroup
        nested_fields = BudgetItemGroupSerializer.Meta.fields
        fields = nested_fields + ('children', )
        response = {
            'children': (
                SubAccountSimpleSerializer, {'many': True, 'nested': True})
        }

    def validate_children(self, value):
        # In the case of a POST request, the parent will be in the context. In
        # the case of a PATCH request, the instance will be non-null.
        parent = self.context.get('parent')
        if parent is None:
            parent = self.instance.parent
        for subaccount in value:
            if subaccount.parent != parent:
                raise exceptions.ValidationError(
                    "The subaccount %s does not belong to the same parent "
                    "that the group does (%s)." % (subaccount.pk, parent.pk)
                )
        return value


class SubAccountSerializer(SubAccountSimpleSerializer):
    type = serializers.CharField(read_only=True)
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
    rate = serializers.FloatField(required=False, allow_null=False)
    multiplier = serializers.FloatField(required=False, allow_null=False)
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    unit = serializers.ChoiceField(
        required=False,
        choices=SubAccount.UNITS
    )
    unit_name = serializers.CharField(read_only=True)
    budget = serializers.PrimaryKeyRelatedField(read_only=True)
    ancestors = AncestorSerializer(many=True, read_only=True)
    account = serializers.IntegerField(read_only=True, source='account.pk')
    object_id = serializers.IntegerField(read_only=True)
    parent_type = serializers.ChoiceField(
        choices=["account", "subaccount"],
        read_only=True
    )
    subaccounts = SubAccountSimpleSerializer(many=True, read_only=True)
    group = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=SubAccountGroup.objects.all(),
        allow_null=True
    )

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + (
            'identifier', 'name', 'description', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'quantity', 'rate', 'multiplier',
            'unit', 'unit_name', 'account', 'object_id', 'parent_type',
            'ancestors', 'estimated', 'subaccounts', 'actual', 'variance',
            'budget', 'type', 'group')

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


class SubAccountChangeSerializer(SubAccountSerializer):
    id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=SubAccount.objects.all()
    )

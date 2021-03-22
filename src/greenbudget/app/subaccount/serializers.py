from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)
from greenbudget.app.common.serializers import AncestorSerializer
from greenbudget.app.user.serializers import UserSerializer

from .models import SubAccount, SubAccountGroup


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


class SubAccountGroupSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    created_by = UserSerializer(nested=True, read_only=True)
    updated_by = UserSerializer(nested=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    color = serializers.ChoiceField(
        required=True,
        choices=[
            "#797695",
            "#ff7165",
            "#80cbc4",
            "#ce93d8",
            "#fed835",
            "#c87987",
            "#69f0ae",
            "#a1887f",
            "#81d4fa",
            "#f75776",
            "#66bb6a",
            "#58add6"
        ]
    )
    # TODO: We have to build in validation that ensures that the sub accounts
    # in a group all belong to the same parent!
    subaccounts = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=SubAccount.objects.all()
    )

    class Meta:
        model = SubAccountGroup
        nested_fields = (
            'id', 'name', 'created_by', 'created_at', 'updated_by',
            'updated_at', 'color')
        fields = nested_fields + ('subaccounts', )
        response = {
            'subaccounts': (
                SubAccountSimpleSerializer, {'many': True, 'nested': True})
        }

    def validate_name(self, value):
        # In the case of a POST request, the parent will be in the context. In
        # the case of a PATCH request, the instance will be non-null.
        parent = self.context.get('parent')
        if parent is None:
            parent = self.instance.parent
        validator = serializers.UniqueTogetherValidator(
            queryset=parent.subaccount_groups.all(),
            fields=('name', ),
        )
        validator({'name': value}, self)
        return value

    def validate_subaccounts(self, value):
        # In the case of a POST request, the parent will be in the context. In
        # the case of a PATCH request, the instance will be non-null.
        parent = self.context.get('parent')
        if parent is None:
            parent = self.instance.parent
        for subaccount in value:
            if subaccount.parent != parent:
                raise exceptions.ValidationError(
                    "The subaccount %s does not belong to the same parent "
                    "that the group does (%s)." % (subaccount.pk, parent)
                )
        return value


class SubAccountSerializer(SubAccountSimpleSerializer):
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    type = serializers.CharField(read_only=True)
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
        queryset=SubAccountGroup.objects.all()
    )

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + (
            'identifier', 'name', 'description', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'quantity', 'rate', 'multiplier',
            'unit', 'unit_name', 'account', 'object_id', 'parent_type',
            'ancestors', 'estimated', 'subaccounts', 'actual', 'variance',
            'budget', 'type', 'group')
        response = {
            'group': (SubAccountGroupSerializer, {'nested': True})
        }

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

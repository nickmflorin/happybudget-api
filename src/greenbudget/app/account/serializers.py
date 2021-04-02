from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.common.serializers import EntitySerializer
from greenbudget.app.budget_item.serializers import (
    BudgetItemGroupSerializer,
    BudgetItemSimpleSerializer
)
from greenbudget.app.subaccount.serializers import (
    SubAccountSimpleSerializer,
    AbstractBulkUpdateSubAccountsSerializer,
    AbstractBulkCreateSubAccountsSerializer
)
from greenbudget.app.user.models import User
from greenbudget.app.user.serializers import UserSerializer

from .models import Account, AccountGroup


class AccountBulkCreateSubAccountsSerializer(
        AbstractBulkCreateSubAccountsSerializer):

    class Meta:
        model = Account
        fields = AbstractBulkCreateSubAccountsSerializer.Meta.fields


class AccountBulkUpdateSubAccountsSerializer(
        AbstractBulkUpdateSubAccountsSerializer):

    class Meta:
        model = Account
        fields = AbstractBulkCreateSubAccountsSerializer.Meta.fields


class AccountGroupSerializer(BudgetItemGroupSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Account.objects.all()
    )

    class Meta:
        model = AccountGroup
        nested_fields = BudgetItemGroupSerializer.Meta.fields
        fields = nested_fields + ('children', )
        response = {
            'children': (
                BudgetItemSimpleSerializer, {'many': True, 'nested': True})
        }

    def validate_children(self, value):
        # In the case of a POST request, the parent will be in the context. In
        # the case of a PATCH request, the instance will be non-null.
        budget = self.context.get('parent')
        if budget is None:
            budget = self.instance.budget
        for account in value:
            if account.budget != budget:
                raise exceptions.ValidationError(
                    "The account %s does not belong to the same budget "
                    "that the group does (%s)." % (account.pk, budget.pk)
                )
        return value


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
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    subaccounts = SubAccountSimpleSerializer(many=True, read_only=True)
    group = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=AccountGroup.objects.all(),
        allow_null=True
    )

    class Meta:
        model = Account
        fields = (
            'id', 'identifier', 'description', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'access', 'budget', 'ancestors',
            'estimated', 'subaccounts', 'actual', 'variance', 'type', 'group',
            'siblings')

    def validate_identifier(self, value):
        # In the case that the serializer is nested and being used in a write
        # context, we do not have access to the context.  Validation will
        # have to be done by the serializer using this serializer in its nested
        # form.
        if self._nested is not True:
            budget = self.context.get('budget')
            if budget is None:
                budget = self.instance.budget
            validator = serializers.UniqueTogetherValidator(
                queryset=Account.objects.filter(budget=budget),
                fields=('identifier', ),
            )
            validator({'identifier': value, 'budget': budget}, self)
        return value


class AccountBulkChangeSerializer(AccountSerializer):
    id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Account.objects.all()
    )

    def validate_id(self, instance):
        budget = self.parent.parent.instance
        if budget != instance.budget:
            raise exceptions.ValidationError(
                "The account %s does not belong to budget %s."
                % (instance.pk, budget.pk)
            )
        return instance

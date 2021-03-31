from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.common.serializers import AncestorSerializer
from greenbudget.app.budget_item.serializers import (
    BudgetItemGroupSerializer, BudgetItemSimpleSerializer)
from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.subaccount.serializers import (
    SubAccountBulkChangeSerializer,
    SubAccountSimpleSerializer,
    SubAccountSerializer
)
from greenbudget.app.user.models import User
from greenbudget.app.user.serializers import UserSerializer

from .models import Account, AccountGroup


class AccountBulkCreateSubAccountsSerializer(serializers.ModelSerializer):
    data = SubAccountSerializer(many=True, nested=True)

    class Meta:
        model = Account
        fields = ('data', )

    def update(self, instance, validated_data):
        subaccounts = []
        for payload in validated_data['data']:
            serializer = SubAccountSerializer(data=payload, context={
                'budget': instance.budget
            })
            serializer.is_valid(raise_exception=True)
            # Note that the updated_by argument is the user updating the
            # Account by adding new SubAccount(s), so the SubAccount(s) should
            # be denoted as having been created by this user.
            subaccount = serializer.save(
                updated_by=validated_data['updated_by'],
                created_by=validated_data['updated_by'],
                object_id=instance.pk,
                content_type=ContentType.objects.get_for_model(SubAccount),
                parent=instance,
                budget=instance.budget
            )
            subaccounts.append(subaccount)
        return subaccounts


class AccountBulkUpdateSubAccountsSerializer(serializers.ModelSerializer):
    data = SubAccountBulkChangeSerializer(many=True)

    class Meta:
        model = Account
        fields = ('data', )

    def validate_data(self, data):
        grouped = {}
        for change in data:
            instance = change['id']
            del change['id']
            if instance.parent != self.instance:
                raise exceptions.ValidationError(
                    "The sub-account %s does not belong to account %s."
                    % (instance.pk, self.instance.pk)
                )
            if instance.pk not in grouped:
                grouped[instance.pk] = {
                    **{'instance': instance}, **change}
            else:
                grouped[instance.pk] = {
                    **grouped[instance.pk],
                    **{'instance': instance},
                    **change
                }
        return grouped

    def update(self, instance, validated_data):
        for id, change in validated_data['data'].items():
            subaccount = change['instance']
            del change['instance']
            serializer = SubAccountSerializer(
                instance=subaccount,
                data=change,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=validated_data['updated_by'])
        return instance


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
    ancestors = AncestorSerializer(many=True, read_only=True)
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
            'estimated', 'subaccounts', 'actual', 'variance', 'type', 'group')

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

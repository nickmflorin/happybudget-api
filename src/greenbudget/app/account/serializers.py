from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.budget.models import BaseBudget
from greenbudget.app.common.serializers import (
    EntitySerializer,
    AbstractBulkUpdateSerializer,
    create_bulk_create_serializer
)
from greenbudget.app.group.models import (
    BudgetAccountGroup,
    TemplateAccountGroup
)
from greenbudget.app.user.models import User

from .models import Account, BudgetAccount, TemplateAccount


class AccountSimpleSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    type = serializers.CharField(read_only=True)
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )

    class Meta:
        model = Account
        fields = ('id', 'identifier', 'type', 'description')


class AccountSerializer(AccountSimpleSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    budget = serializers.PrimaryKeyRelatedField(read_only=True)
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)
    estimated = serializers.FloatField(read_only=True)
    subaccounts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(AccountSimpleSerializer.Meta):
        fields = AccountSimpleSerializer.Meta.fields + (
            'created_by', 'updated_by', 'created_at', 'updated_at', 'budget',
            'ancestors', 'estimated', 'subaccounts', 'type', 'siblings')


class BudgetAccountSerializer(AccountSerializer):
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    access = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.active(),
        required=False
    )
    group = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=BudgetAccountGroup.objects.all()
    )

    class Meta:
        model = BudgetAccount
        fields = AccountSerializer.Meta.fields + (
            'actual', 'variance', 'access', 'group')


class TemplateAccountSerializer(AccountSerializer):
    group = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=TemplateAccountGroup.objects.all()
    )

    class Meta:
        model = TemplateAccount
        fields = AccountSerializer.Meta.fields + ('group', )


def create_bulk_create_accounts_serializer(model_cls):
    data_serializer = BudgetAccountSerializer
    if model_cls is TemplateAccount:
        data_serializer = TemplateAccountSerializer

    base_serializer = create_bulk_create_serializer(data_serializer)

    class BulkCreateAccountsSerializer(base_serializer):

        class Meta(base_serializer.Meta):
            model = BaseBudget

        def get_serializer_context(self, instance):
            return {'budget': instance}

        def perform_save(self, serializer, instance, validated_data):
            return serializer.save(
                updated_by=validated_data['updated_by'],
                created_by=validated_data['updated_by'],
                budget=instance
            )

    return BulkCreateAccountsSerializer


def create_budget_account_bulk_change_serializer(model_cls):
    base_serializer = BudgetAccountSerializer
    if model_cls is TemplateAccount:
        base_serializer = TemplateAccountSerializer

    class AccountBulkChangeSerializer(base_serializer):
        id = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=model_cls.objects.all()
        )

        def validate_id(self, instance):
            budget = self.parent.parent.instance
            if budget != instance.budget:
                raise exceptions.ValidationError(
                    "The account %s does not belong to budget %s."
                    % (instance.pk, budget.pk)
                )
            return instance
    return AccountBulkChangeSerializer


def create_bulk_update_accounts_serializer(model_cls):
    class BulkUpdateAccountsSerializer(AbstractBulkUpdateSerializer):
        data = create_budget_account_bulk_change_serializer(model_cls)(
            many=True, nested=True)

        class Meta:
            model = BaseBudget
            fields = ('data', )

        def update(self, instance, validated_data):
            for account, change in validated_data['data']:
                serializer = AccountSerializer(
                    instance=account,
                    data=change,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save(updated_by=validated_data['updated_by'])
            return instance
    return BulkUpdateAccountsSerializer

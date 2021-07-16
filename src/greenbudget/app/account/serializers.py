from rest_framework import serializers

from greenbudget.lib.drf.serializers import (
    ModelSerializer)

from greenbudget.app.budget.serializers import EntitySerializer
from greenbudget.app.group.models import BudgetAccountGroup, TemplateAccountGroup  # noqa
from greenbudget.app.subaccount.serializers import SubAccountPdfSerializer
from greenbudget.app.user.models import User

from .models import Account, BudgetAccount, TemplateAccount


class AccountSimpleSerializer(ModelSerializer):
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
    estimated = serializers.FloatField(read_only=True)
    subaccounts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(AccountSimpleSerializer.Meta):
        fields = AccountSimpleSerializer.Meta.fields + (
            'created_by', 'updated_by', 'created_at', 'updated_at', 'estimated',
            'subaccounts')


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
        queryset=BudgetAccountGroup.objects.all(),
        write_only=True
    )

    class Meta:
        model = BudgetAccount
        fields = AccountSerializer.Meta.fields + (
            'actual', 'variance', 'access', 'group')


class BudgetAccountDetailSerializer(BudgetAccountSerializer):
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)

    class Meta(BudgetAccountSerializer.Meta):
        fields = BudgetAccountSerializer.Meta.fields + (
            "ancestors", "siblings")


class TemplateAccountSerializer(AccountSerializer):
    group = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=TemplateAccountGroup.objects.all(),
        write_only=True
    )

    class Meta:
        model = TemplateAccount
        fields = AccountSerializer.Meta.fields + ('group', )


class TemplateAccountDetailSerializer(TemplateAccountSerializer):
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)

    class Meta(TemplateAccountSerializer.Meta):
        fields = TemplateAccountSerializer.Meta.fields + (
            "ancestors", "siblings")


class AccountPdfSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    subaccounts = SubAccountPdfSerializer(many=True, read_only=True)
    group = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = BudgetAccount
        fields = ('id', 'identifier', 'description', 'actual', 'variance',
            'estimated', 'subaccounts', 'group')
        read_only_fields = fields

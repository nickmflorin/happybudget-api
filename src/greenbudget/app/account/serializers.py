from rest_framework import serializers

from greenbudget.lib.drf.serializers import (
    ModelSerializer)

from greenbudget.app.budget.serializers import EntitySerializer
from greenbudget.app.group.models import (
    BudgetAccountGroup,
    TemplateAccountGroup
)
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

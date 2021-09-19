from rest_framework import serializers

from greenbudget.lib.drf.serializers import (
    ModelSerializer)

from greenbudget.app.budgeting.fields import TableChildrenPrimaryKeyRelatedField
from greenbudget.app.budgeting.serializers import EntitySerializer
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
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
    actual = serializers.FloatField(read_only=True)
    fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    group = TableChildrenPrimaryKeyRelatedField(
        obj_name='Account',
        required=False,
        allow_null=True,
        child_instance_cls=lambda parent: Group.child_instance_cls_for_parent(
            parent),
        write_only=True,
    )

    class Meta(AccountSimpleSerializer.Meta):
        fields = AccountSimpleSerializer.Meta.fields + (
            'created_by', 'updated_by', 'created_at', 'updated_at', 'estimated',
            'children', 'fringe_contribution', 'markup_contribution', 'actual',
            'group')


class BudgetAccountSerializer(AccountSerializer):
    access = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.active(),
        required=False
    )

    class Meta:
        model = BudgetAccount
        fields = AccountSerializer.Meta.fields + ('access',)


class BudgetAccountDetailSerializer(BudgetAccountSerializer):
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)

    class Meta(BudgetAccountSerializer.Meta):
        fields = BudgetAccountSerializer.Meta.fields + (
            "ancestors", "siblings")


class TemplateAccountSerializer(AccountSerializer):
    class Meta:
        model = TemplateAccount
        fields = AccountSerializer.Meta.fields


class TemplateAccountDetailSerializer(TemplateAccountSerializer):
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)

    class Meta(TemplateAccountSerializer.Meta):
        fields = TemplateAccountSerializer.Meta.fields + (
            "ancestors", "siblings")


class AccountPdfSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    identifier = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    children = SubAccountPdfSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = BudgetAccount
        fields = ('id', 'identifier', 'description', 'actual',
            'estimated', 'children', 'groups', 'type', 'fringe_contribution',
            'markup_contribution')
        read_only_fields = fields

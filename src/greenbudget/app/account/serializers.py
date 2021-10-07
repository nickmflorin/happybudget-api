from rest_framework import serializers

from greenbudget.lib.drf.serializers import (
    ModelSerializer)

from greenbudget.app.budgeting.fields import TableChildrenPrimaryKeyRelatedField
from greenbudget.app.budgeting.serializers import (
    SimpleEntityPolymorphicSerializer)
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.markup.serializers import MarkupSerializer
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

    accumulated_value = serializers.FloatField(read_only=True)
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)

    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    group = TableChildrenPrimaryKeyRelatedField(
        obj_name='Group',
        required=False,
        allow_null=True,
        child_instance_cls=Group,
        write_only=True,
    )

    class Meta(AccountSimpleSerializer.Meta):
        fields = AccountSimpleSerializer.Meta.fields + (
            'created_by', 'updated_by', 'created_at', 'updated_at',
            'children', 'nominal_value', 'group'
        ) + Account.CALCULATED_FIELDS


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
    ancestors = SimpleEntityPolymorphicSerializer(many=True, read_only=True)
    siblings = SimpleEntityPolymorphicSerializer(many=True, read_only=True)

    class Meta(BudgetAccountSerializer.Meta):
        fields = BudgetAccountSerializer.Meta.fields + (
            "ancestors", "siblings")


class TemplateAccountSerializer(AccountSerializer):
    class Meta:
        model = TemplateAccount
        fields = AccountSerializer.Meta.fields


class TemplateAccountDetailSerializer(TemplateAccountSerializer):
    ancestors = SimpleEntityPolymorphicSerializer(many=True, read_only=True)
    siblings = SimpleEntityPolymorphicSerializer(many=True, read_only=True)

    class Meta(TemplateAccountSerializer.Meta):
        fields = TemplateAccountSerializer.Meta.fields + (
            "ancestors", "siblings")


class AccountPdfSerializer(AccountSimpleSerializer):
    type = serializers.CharField(read_only=True, source='pdf_type')
    accumulated_value = serializers.FloatField(read_only=True)
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    children_markups = MarkupSerializer(many=True, read_only=True)
    children = SubAccountPdfSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = BudgetAccount
        fields = AccountSimpleSerializer.Meta.fields \
            + Account.CALCULATED_FIELDS \
            + ('children', 'groups', 'nominal_value', 'children_markups')
        read_only_fields = fields

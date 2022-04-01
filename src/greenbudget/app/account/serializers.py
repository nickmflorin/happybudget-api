from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from greenbudget.app.budgeting.serializers import EntityAncestorSerializer
from greenbudget.app.group.fields import GroupField
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.markup.serializers import MarkupSerializer
from greenbudget.app.subaccount.serializers import SubAccountPdfSerializer
from greenbudget.app.serializers import ModelSerializer
from greenbudget.app.tabling.serializers import row_order_serializer

from .models import Account, BudgetAccount, TemplateAccount


class AccountSimpleSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    domain = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )

    class Meta:
        model = Account
        fields = ('id', 'identifier', 'type', 'description', 'domain')


class AccountSerializer(AccountSimpleSerializer):
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    group = GroupField(
        table_filter=lambda ctx: {
            'object_id': ctx.parent.id,
            'content_type_id': ContentType.objects.get_for_model(
                type(ctx.parent)).id,
        },
        required=False,
        allow_null=True,
        write_only=True,
    )
    order = serializers.CharField(read_only=True)

    class Meta(AccountSimpleSerializer.Meta):
        fields = AccountSimpleSerializer.Meta.fields + (
            'children', 'nominal_value', 'group', 'actual', 'order',
            'markup_contribution', 'accumulated_markup_contribution',
            'accumulated_fringe_contribution',
        )


class BudgetAccountSerializer(AccountSerializer):
    class Meta(AccountSerializer.Meta):
        model = BudgetAccount


@row_order_serializer(table_filter=lambda d: {'parent_id': d.parent.id})
class BudgetAccountDetailSerializer(BudgetAccountSerializer):
    ancestors = EntityAncestorSerializer(many=True, read_only=True)
    table = AccountSimpleSerializer(many=True, read_only=True)

    class Meta(BudgetAccountSerializer.Meta):
        fields = BudgetAccountSerializer.Meta.fields + (
            "ancestors", "table")


class TemplateAccountSerializer(AccountSerializer):
    class Meta(AccountSerializer.Meta):
        model = TemplateAccount


@row_order_serializer(table_filter=lambda d: {'parent_id': d.parent.id})
class TemplateAccountDetailSerializer(TemplateAccountSerializer):
    ancestors = EntityAncestorSerializer(many=True, read_only=True)
    table = AccountSimpleSerializer(many=True, read_only=True)

    class Meta(TemplateAccountSerializer.Meta):
        fields = TemplateAccountSerializer.Meta.fields + (
            "ancestors", "table")


class AccountPdfSerializer(AccountSimpleSerializer):
    type = serializers.CharField(read_only=True, source='pdf_type')
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    children_markups = MarkupSerializer(many=True, read_only=True)
    children = SubAccountPdfSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)
    order = serializers.CharField(read_only=True)

    class Meta:
        model = BudgetAccount
        fields = AccountSimpleSerializer.Meta.fields \
            + ('children', 'groups', 'nominal_value', 'children_markups',
                'markup_contribution', 'actual', 'order',
                'accumulated_markup_contribution',
                'accumulated_fringe_contribution',
            )
        read_only_fields = fields

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, exceptions

from greenbudget.app.budgeting.serializers import EntityAncestorSerializer
from greenbudget.app.contact.models import Contact
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.fields import GroupField
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.io.models import Attachment
from greenbudget.app.io.serializers import SimpleAttachmentSerializer
from greenbudget.app.markup.serializers import MarkupSerializer
from greenbudget.app.tabling.serializers import row_order_serializer
from greenbudget.app.tagging.fields import TagField
from greenbudget.app.tagging.serializers import TagSerializer, ColorSerializer
from greenbudget.app.user.fields import UserFilteredQuerysetPKField

from .models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount, SubAccountUnit)


class SubAccountUnitSerializer(TagSerializer):
    color = ColorSerializer(read_only=True)

    class Meta:
        model = SubAccountUnit
        fields = TagSerializer.Meta.fields + ("color", )


class SubAccountAsOwnerSerializer(serializers.ModelSerializer):
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
        model = SubAccount
        fields = ('id', 'identifier', 'type', 'description')


class SubAccountSimpleSerializer(SubAccountAsOwnerSerializer):
    domain = serializers.CharField(read_only=True)

    class Meta(SubAccountAsOwnerSerializer.Meta):
        fields = SubAccountAsOwnerSerializer.Meta.fields + ('domain', )


class SubAccountSerializer(SubAccountSimpleSerializer):
    quantity = serializers.FloatField(required=False, allow_null=True)
    rate = serializers.FloatField(required=False, allow_null=True)
    multiplier = serializers.FloatField(required=False, allow_null=True)
    nominal_value = serializers.FloatField(read_only=True)
    fringe_contribution = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
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
    unit = TagField(
        serializer_class=SubAccountUnitSerializer,
        queryset=SubAccountUnit.objects.all(),
        required=False,
        allow_null=True
    )
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    object_id = serializers.IntegerField(read_only=True)
    parent_type = serializers.ChoiceField(
        choices=["account", "subaccount"],
        read_only=True
    )
    fringes = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Fringe.objects.all()
    )
    contact = UserFilteredQuerysetPKField(
        required=False,
        allow_null=True,
        queryset=Contact.objects.all(),
        user_field='created_by'
    )
    order = serializers.CharField(read_only=True)

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + (
            'quantity', 'rate', 'multiplier', 'unit', 'object_id',
            'parent_type', 'children', 'fringes', 'group', 'order',
            'nominal_value', 'actual', 'fringe_contribution',
            'markup_contribution', 'accumulated_markup_contribution',
            'accumulated_fringe_contribution',
        )

    def validate(self, attrs):
        if self.instance is not None and self.instance.children.count() != 0:
            if any([field in attrs for field in self.instance.DERIVING_FIELDS]):
                raise exceptions.ValidationError(
                    "Field can only be updated when the sub account is not "
                    "derived."
                )
        if 'rate' in attrs and 'quantity' not in attrs:
            # On a PATCH request to update the SubAccount, we automatically
            # assign quantity = 1.0 if the rate is being assigned but the
            # quantity is not.
            if (self.instance is not None and self.instance.quantity is None) \
                    or self.instance is None:
                attrs.update(quantity=1.0)

        return super().validate(attrs)


class BudgetSubAccountSerializer(SubAccountSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        queryset=Attachment.objects.all(),
        required=False,
        many=True
    )
    contact = UserFilteredQuerysetPKField(
        required=False,
        allow_null=True,
        queryset=Contact.objects.all(),
        user_field='created_by'
    )

    class Meta(SubAccountSerializer.Meta):
        model = BudgetSubAccount
        fields = SubAccountSerializer.Meta.fields + ('attachments', 'contact', )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(attachments=SimpleAttachmentSerializer(
            instance=instance.attachments.all(),
            many=True
        ).data)
        return data


@row_order_serializer(table_filter=lambda d: {
    'object_id': d.parent.id,
    'content_type_id': ContentType.objects.get_for_model(type(d.parent)).id
})
class BudgetSubAccountDetailSerializer(BudgetSubAccountSerializer):
    ancestors = EntityAncestorSerializer(many=True, read_only=True)
    table = SubAccountSimpleSerializer(many=True, read_only=True)

    class Meta(BudgetSubAccountSerializer.Meta):
        model = BudgetSubAccount
        fields = BudgetSubAccountSerializer.Meta.fields + (
            'ancestors', 'table')


class TemplateSubAccountSerializer(SubAccountSerializer):
    class Meta(SubAccountSerializer.Meta):
        model = TemplateSubAccount
        fields = SubAccountSerializer.Meta.fields


@row_order_serializer(table_filter=lambda d: {
    'object_id': d.parent.id,
    'content_type_id': ContentType.objects.get_for_model(type(d.parent)).id
})
class TemplateSubAccountDetailSerializer(TemplateSubAccountSerializer):
    ancestors = EntityAncestorSerializer(many=True, read_only=True)
    table = SubAccountSimpleSerializer(many=True, read_only=True)

    class Meta(TemplateSubAccountSerializer.Meta):
        model = TemplateSubAccount
        fields = TemplateSubAccountSerializer.Meta.fields + (
            'ancestors', 'table')


class SubAccountPdfSerializer(SubAccountSimpleSerializer):
    type = serializers.CharField(read_only=True, source='pdf_type')
    quantity = serializers.FloatField(read_only=True)
    rate = serializers.FloatField(read_only=True)
    unit = TagField(
        model_cls=SubAccountUnit,
        read_only=True,
        serializer_class=SubAccountUnitSerializer
    )
    contact = UserFilteredQuerysetPKField(
        required=False,
        allow_null=True,
        queryset=Contact.objects.all(),
        user_field='created_by'
    )
    children = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True, read_only=True)
    children_markups = MarkupSerializer(many=True, read_only=True)
    nominal_value = serializers.FloatField(read_only=True)
    fringe_contribution = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    order = serializers.CharField(read_only=True)

    class Meta:
        model = BudgetSubAccount
        fields = SubAccountSimpleSerializer.Meta.fields \
            + (
                'quantity', 'rate', 'multiplier', 'unit', 'children', 'contact',
                'group', 'groups', 'children_markups', 'nominal_value', 'actual',
                'fringe_contribution', 'markup_contribution', 'order',
                'accumulated_markup_contribution',
                'accumulated_fringe_contribution'
            )
        read_only_fields = fields

    def get_children(self, instance):
        return self.__class__(instance.children.all(), many=True).data

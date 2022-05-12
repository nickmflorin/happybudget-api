from rest_framework import serializers

from happybudget.lib.drf.fields import GenericRelatedField
from happybudget.lib.drf.serializers import PolymorphicNonPolymorphicSerializer

from happybudget.app.budget.serializers import BudgetSimpleSerializer
from happybudget.app.contact.models import Contact
from happybudget.app.io.models import Attachment
from happybudget.app.io.serializers import SimpleAttachmentSerializer
from happybudget.app.markup.models import Markup
from happybudget.app.markup.serializers import MarkupSimpleSerializer
from happybudget.app.tabling.serializers import row_order_serializer
from happybudget.app.tagging.fields import TagField
from happybudget.app.tagging.serializers import TagSerializer, ColorSerializer
from happybudget.app.serializers import ModelSerializer
from happybudget.app.subaccount.models import BudgetSubAccount
from happybudget.app.subaccount.serializers import SubAccountAsOwnerSerializer
from happybudget.app.user.fields import OwnershipPrimaryKeyRelatedField

from .models import Actual, ActualType


class ActualOwnerSerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        Markup: "happybudget.app.markup.serializers.MarkupSimpleSerializer",
        BudgetSubAccount: (
            "happybudget.app.subaccount.serializers."
            "SubAccountAsOwnerSerializer"
        ),
    }


class ActualOwnerField(GenericRelatedField):
    def get_queryset(self, data):
        qs = super().get_queryset(data)
        # When bulk creating Actuals, even though the request method will be
        # PATCH there will not be an instance on the parent serializer.
        if self.context['request'].method == 'PATCH' \
                and self.context.get('bulk_create_context', False) is not True \
                and self.context.get('bulk_update_context', False) is not True:
            budget = self.parent.instance.budget
        else:
            assert 'budget' in self.context, \
                "The budget must be provided in context when using %s in " \
                "a POST context or a PATCH context during a bulk operation." \
                % self.__class__.__name__
            budget = self.context["budget"]
        return qs.filter_by_budget(budget)

    def to_representation(self, instance):
        if isinstance(instance, BudgetSubAccount):
            return SubAccountAsOwnerSerializer(instance=instance).data
        return MarkupSimpleSerializer(instance=instance).data


class ActualTypeSerializer(TagSerializer):
    color = ColorSerializer(read_only=True)

    class Meta:
        model = ActualType
        fields = TagSerializer.Meta.fields + ("color", )


class TaggedActualSerializer(ModelSerializer):
    type = serializers.CharField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    date = serializers.DateField(
        required=False,
        allow_null=True
    )
    value = serializers.FloatField(required=False, allow_null=True)
    owner = ActualOwnerField(
        required=False,
        allow_null=True,
        model_classes={'subaccount': BudgetSubAccount, 'markup': Markup}
    )
    budget = BudgetSimpleSerializer()

    class Meta:
        model = Actual
        fields = (
            'id', 'name', 'value', 'date', 'owner', 'type', 'budget')
        read_only_fields = fields


class ActualSerializer(TaggedActualSerializer):
    order = serializers.CharField(read_only=True)
    notes = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    purchase_order = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True
    )
    payment_id = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True
    )
    attachments = serializers.PrimaryKeyRelatedField(
        queryset=Attachment.objects.all(),
        required=False,
        many=True
    )
    actual_type = TagField(
        serializer_class=ActualTypeSerializer,
        queryset=ActualType.objects.all(),
        required=False,
        allow_null=True
    )
    contact = OwnershipPrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=Contact.objects.all(),
    )

    class Meta:
        model = Actual
        fields = (
            'id', 'name', 'purchase_order', 'date', 'payment_id', 'value',
            'actual_type', 'contact', 'owner', 'type', 'attachments',
            'notes', 'order')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(attachments=SimpleAttachmentSerializer(
            instance=instance.attachments.all(),
            many=True
        ).data)
        return data


@row_order_serializer(table_filter=lambda d: {'budget_id': d.budget.id})
class ActualDetailSerializer(ActualSerializer):
    pass

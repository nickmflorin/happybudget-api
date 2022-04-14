from rest_framework import serializers

from greenbudget.lib.drf.fields import GenericRelatedField
from greenbudget.lib.drf.serializers import PolymorphicNonPolymorphicSerializer

from greenbudget.app.budget.serializers import BudgetSimpleSerializer
from greenbudget.app.contact.models import Contact
from greenbudget.app.io.models import Attachment
from greenbudget.app.io.serializers import SimpleAttachmentSerializer
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSimpleSerializer
from greenbudget.app.tabling.serializers import row_order_serializer
from greenbudget.app.tagging.fields import TagField
from greenbudget.app.tagging.serializers import TagSerializer, ColorSerializer
from greenbudget.app.serializers import ModelSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.serializers import SubAccountAsOwnerSerializer
from greenbudget.app.user.fields import OwnershipPrimaryKeyRelatedField

from .models import Actual, ActualType


class ActualOwnerSerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        Markup: "greenbudget.app.markup.serializers.MarkupSimpleSerializer",
        BudgetSubAccount: (
            "greenbudget.app.subaccount.serializers."
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
            if 'budget' not in self.context:
                raise Exception(
                    "The budget must be provided in context when using %s in "
                    "a POST context or a PATCH context during a bulk operation."
                    % self.__class__.__name__
                )
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

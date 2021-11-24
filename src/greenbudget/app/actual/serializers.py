from rest_framework import serializers

from greenbudget.lib.drf.fields import GenericRelatedField
from greenbudget.lib.drf.serializers import ModelSerializer

from greenbudget.app.contact.models import Contact
from greenbudget.app.io.models import Attachment
from greenbudget.app.io.serializers import SimpleAttachmentSerializer
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSimpleSerializer
from greenbudget.app.tabling.serializers import row_order_serializer
from greenbudget.app.tagging.fields import TagField
from greenbudget.app.tagging.serializers import TagSerializer, ColorSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.serializers import SubAccountSimpleSerializer
from greenbudget.app.user.fields import UserFilteredQuerysetPKField

from .models import Actual, ActualType


class OwnerTreeNodeSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        # The subset is the set of SubAccount(s) that have been filtered by
        # the search.  Only these SubAccount(s) will be included as children
        # to each node of the tree.
        self._subset = kwargs.pop('subset')
        self._search_path = kwargs.pop('search_path')
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        assert isinstance(instance, (Markup, BudgetSubAccount))
        if isinstance(instance, Markup):
            data = MarkupSimpleSerializer(instance).data
        else:
            data = SubAccountSimpleSerializer(instance).data
        data.update(in_search_path=instance in self._search_path)
        if isinstance(instance, BudgetSubAccount):
            data.update(children=[
                self.__class__(
                    instance=child,
                    search_path=self._search_path,
                    subset=self._subset
                ).data
                for child in self._subset if child.parent == instance
            ])
        return data


class ActualOwnerField(GenericRelatedField):

    def get_queryset(self, data):
        qs = super().get_queryset(data)
        request = self.context['request']
        # When bulk creating Actuals, even though the request method will be
        # PATCH there will not be an instance on the parent serializer.
        if request.method == 'PATCH' \
                and self.context.get('bulk_create_context', False) is not True \
                and self.context.get('bulk_update_context', False) is not True:
            budget = self.parent.instance.budget
        else:
            if 'budget' not in self.context:
                raise Exception(
                    "The budget must be provided in context when using %s in "
                    "a POST context or a PATCH context during a bulk operaiton."
                    % self.__class__.__name__
                )
            budget = self.context["budget"]
        return qs.filter_by_budget(budget)

    def to_representation(self, instance):
        if isinstance(instance, BudgetSubAccount):
            return SubAccountSimpleSerializer(instance=instance).data
        return MarkupSimpleSerializer(instance=instance).data


class ActualTypeSerializer(TagSerializer):
    color = ColorSerializer(read_only=True)

    class Meta:
        model = ActualType
        fields = TagSerializer.Meta.fields + ("color", )


class ActualSerializer(ModelSerializer):
    type = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
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
    date = serializers.DateTimeField(
        required=False,
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
    value = serializers.FloatField(required=False, allow_null=True)
    actual_type = TagField(
        serializer_class=ActualTypeSerializer,
        queryset=ActualType.objects.all(),
        required=False,
        allow_null=True
    )
    owner = ActualOwnerField(
        required=False,
        allow_null=True,
        model_classes={'subaccount': BudgetSubAccount, 'markup': Markup}
    )
    contact = UserFilteredQuerysetPKField(
        required=False,
        allow_null=True,
        queryset=Contact.objects.all(),
        user_field='created_by'
    )

    class Meta:
        model = Actual
        fields = (
            'id', 'name', 'purchase_order', 'date', 'payment_id', 'value',
            'actual_type', 'contact', 'owner', 'type', 'attachments',
            'notes', 'order')
        response = {
            'attachments': (
                SimpleAttachmentSerializer,
                {'many': True}
            )
        }


@row_order_serializer(table_filter=lambda d: {'budget_id': d['budget'].id})
class ActualDetailSerializer(ActualSerializer):
    pass

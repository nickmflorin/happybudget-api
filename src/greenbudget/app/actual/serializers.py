from rest_framework import serializers

from greenbudget.lib.drf.fields import ModelChoiceField, GenericRelatedField
from greenbudget.lib.drf.serializers import (
    ModelSerializer)

from greenbudget.app.contact.models import Contact
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSimpleSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.serializers import SubAccountSimpleSerializer
from greenbudget.app.user.fields import UserFilteredQuerysetPKField

from .models import Actual


class ActualOwnerField(GenericRelatedField):

    def get_queryset(self, data):
        qs = super().get_queryset(data)
        request = self.context['request']
        # When bulk creating Actuals, even though the request method will be
        # PATCH there will not be an instance on the parent serializer.
        if request.method == 'PATCH' \
                and self.context.get('bulk_create_context', False) is not True:
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


class ActualSerializer(ModelSerializer):
    type = serializers.CharField(read_only=True)
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
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
    value = serializers.FloatField(required=False, allow_null=True)
    payment_method = ModelChoiceField(
        required=False,
        choices=Actual.PAYMENT_METHODS,
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
        user_field='user'
    )

    class Meta:
        model = Actual
        fields = (
            'id', 'description', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'purchase_order', 'date', 'payment_id', 'value',
            'payment_method', 'contact', 'owner', 'type')

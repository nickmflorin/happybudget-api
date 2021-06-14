from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.exceptions import (
    InvalidFieldError, RequiredFieldError)
from greenbudget.lib.rest_framework_utils.fields import ModelChoiceField
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.account.models import Account
from greenbudget.app.budget.serializers import EntitySerializer
from greenbudget.app.subaccount.models import SubAccount

from .models import Actual


class ActualSerializer(EnhancedModelSerializer):
    vendor = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True
    )
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
    account = EntitySerializer(read_only=True, source='parent')
    object_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True
    )
    parent_type = serializers.ChoiceField(
        write_only=True,
        required=False,
        choices=["account", "subaccount"],
        allow_null=True
    )

    class Meta:
        model = Actual
        fields = (
            'id', 'description', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'purchase_order', 'date', 'payment_id', 'value',
            'payment_method', 'object_id', 'parent_type', 'vendor', 'account')

    def validate(self, attrs):
        parent_cls_lookup = {
            'account': Account,
            'subaccount': SubAccount
        }
        if 'parent_type' in attrs or 'object_id' in attrs:
            parent_type = attrs.pop('parent_type', None)
            object_id = attrs.pop('object_id', None)
            if parent_type is None and object_id is None:
                attrs['parent'] = None
            else:
                if parent_type is None or object_id is None:
                    raise RequiredFieldError('parent_type', 'object_id')
                parent_cls = parent_cls_lookup[parent_type]
                try:
                    attrs['parent'] = parent_cls.objects.get(pk=object_id)
                except parent_cls.DoesNotExist:
                    raise InvalidFieldError(
                        "object_id",
                        message="The parent %s does not exist."
                        % object_id
                    )
                budget = self.context.get('budget')
                if budget is None:
                    if self.instance is None:
                        raise Exception(
                            "The budget must be provided in context when using "
                            "the serializer in an update context."
                        )
                    budget = self.instance.budget

                if budget != attrs['parent'].budget:
                    raise InvalidFieldError(
                        "object_id",
                        message=(
                            "The parent %s does not belong to the "
                            "correct budget." % object_id
                        )
                    )
        return attrs

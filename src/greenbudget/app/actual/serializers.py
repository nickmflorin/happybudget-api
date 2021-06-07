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
    object_id = serializers.IntegerField(write_only=True, required=False)
    parent_type = serializers.ChoiceField(
        write_only=True,
        required=False,
        choices=["account", "subaccount"]
    )

    class Meta:
        model = Actual
        fields = (
            'id', 'description', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'purchase_order', 'date', 'payment_id', 'value',
            'payment_method', 'object_id', 'parent_type', 'vendor', 'account')

    def _reconstruct_parent(self, attrs):
        exc = RequiredFieldError.from_data_check(attrs, 'object_id', 'parent_type')  # noqa
        if exc is not None:
            raise exc
        parent_cls = Account if attrs.pop("parent_type") == "account" \
            else SubAccount
        try:
            return parent_cls.objects.get(pk=attrs["object_id"])
        except parent_cls.DoesNotExist:
            raise InvalidFieldError(
                "object_id",
                message="The parent %s does not exist."
                % attrs["object_id"]
            )

    def validate(self, attrs):
        request = self.context["request"]
        bulk_create_context = self.context.get('bulk_create_context', False)
        # In the context of bulk creation, the overall request will be a
        # PATCH request but the serializer is still operating as if it were
        # a POST request because we are creating objects.
        if request.method == "PATCH":
            if bulk_create_context \
                    or ("parent_type" in attrs or "object_id" in attrs):
                attrs['parent'] = self._reconstruct_parent(attrs)

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
                            "correct budget." % attrs["object_id"]
                        )
                    )
        return attrs

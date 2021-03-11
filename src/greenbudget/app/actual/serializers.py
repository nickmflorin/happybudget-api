from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.exceptions import InvalidFieldError
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.account.models import Account
from greenbudget.app.user.serializers import UserSerializer

from .models import Actual


class ActualSerializer(EnhancedModelSerializer):
    vendor = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    created_by = UserSerializer(nested=True, read_only=True)
    updated_by = UserSerializer(nested=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    purchase_order = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    date = serializers.DateTimeField(
        required=False,
        allow_null=False
    )
    # TODO: Should we make this unique across the budget?
    payment_id = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    value = serializers.DecimalField(
        required=False,
        allow_null=False,
        decimal_places=2,
        max_digits=10
    )
    payment_method = serializers.ChoiceField(
        required=False,
        choices=Actual.PAYMENT_METHODS
    )
    payment_method_name = serializers.CharField(read_only=True)
    object_id = serializers.IntegerField()
    parent_type = serializers.ChoiceField(choices=["account", "subaccount"])

    class Meta:
        model = Actual
        fields = (
            'id', 'description', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'purchase_order', 'date', 'payment_id', 'value',
            'payment_method', 'payment_method_name', 'object_id', 'parent_type',
            'vendor')

    def validate(self, attrs):
        parent_cls = (
            Account if attrs.pop("parent_type") == "account" else "subaccount")
        try:
            attrs['parent'] = parent_cls.objects.get(pk=attrs["object_id"])
        except parent_cls.DoesNotExist:
            raise InvalidFieldError(
                "object_id",
                message="The parent %s does not exist." % attrs["object_id"]
            )
        else:
            # In the case of a POST request, the budget will be in the context
            # because it is inferred from the URL.  In the case of a PATCH
            # request, the instance will be non-null and already be associated
            # with a budget.
            budget = self.context.get('budget')
            if budget is None:
                budget = self.instance.budget
            if budget != attrs['parent'].budget:
                raise InvalidFieldError(
                    "object_id",
                    message=(
                        "The parent %s does not belong to the correct budget."
                        % attrs["object_id"]
                    )
                )

        return attrs

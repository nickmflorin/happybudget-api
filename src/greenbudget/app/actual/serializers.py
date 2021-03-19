from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.exceptions import (
    InvalidFieldError, RequiredFieldError)
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.account.models import Account
from greenbudget.app.subaccount.models import SubAccount
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
    value = serializers.FloatField(required=False, allow_null=False)
    payment_method = serializers.ChoiceField(
        required=False,
        choices=Actual.PAYMENT_METHODS
    )
    payment_method_name = serializers.CharField(read_only=True)
    object_id = serializers.IntegerField(required=False)
    parent_type = serializers.ChoiceField(
        required=False,
        choices=["account", "subaccount"]
    )

    class Meta:
        model = Actual
        fields = (
            'id', 'description', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'purchase_order', 'date', 'payment_id', 'value',
            'payment_method', 'payment_method_name', 'object_id', 'parent_type',
            'vendor')

    def validate(self, attrs):
        request = self.context["request"]
        if request.method == "PATCH":
            if "parent_type" in attrs or "object_id" in attrs:
                if "parent_type" not in attrs:
                    raise RequiredFieldError("parent_type")
                if "object_id" not in attrs:
                    raise RequiredFieldError("object_id")

                parent_cls = (
                    Account if attrs.pop("parent_type") == "account"
                    else SubAccount)
                try:
                    attrs['parent'] = parent_cls.objects.get(
                        pk=attrs["object_id"])
                except parent_cls.DoesNotExist:
                    raise InvalidFieldError(
                        "object_id",
                        message="The parent %s does not exist." % attrs["object_id"]  # noqa
                    )
                else:
                    if self.instance.budget != attrs['parent'].budget:
                        raise InvalidFieldError(
                            "object_id",
                            message=(
                                "The parent %s does not belong to the correct "
                                "budget." % attrs["object_id"]
                            )
                        )
        return attrs

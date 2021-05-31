from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.exceptions import (
    InvalidFieldError, RequiredFieldError)
from greenbudget.lib.rest_framework_utils.fields import ModelChoiceField
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.account.models import Account
from greenbudget.app.budget.models import Budget
from greenbudget.app.common.serializers import (
    EntitySerializer, AbstractBulkUpdateSerializer)
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
    # TODO: Should we make this unique across the budget?
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

    def validate(self, attrs):
        # In the case that the serializer is nested and being used in a write
        # context, we do not have access to the context.  Validation will
        # have to be done by the serializer using this serializer in its nested
        # form.
        if self._nested is not True:
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
                            message="The parent %s does not exist."
                            % attrs["object_id"]  # noqa
                        )
                    else:
                        if self.instance.budget != attrs['parent'].budget:
                            raise InvalidFieldError(
                                "object_id",
                                message=(
                                    "The parent %s does not belong to the "
                                    "correct budget." % attrs["object_id"]
                                )
                            )
        return attrs


class ActualBulkChangeSerializer(ActualSerializer):
    id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Actual.objects.all()
    )

    def validate_id(self, instance):
        budget = self.parent.parent.instance
        if budget != instance.budget:
            raise exceptions.ValidationError(
                "The actual %s does not belong to budget %s."
                % (instance.pk, budget.pk)
            )
        return instance


class BulkUpdateActualsSerializer(AbstractBulkUpdateSerializer):
    data = ActualBulkChangeSerializer(many=True, nested=True)

    class Meta:
        model = Budget
        fields = ('data', )

    def update(self, instance, validated_data):
        for actual, change in validated_data['data']:
            serializer = ActualSerializer(
                instance=actual,
                data=change,
                partial=True,
                context={'request': self.context['request']}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=validated_data['updated_by'])
        return instance

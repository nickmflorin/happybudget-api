from rest_framework import serializers

from happybudget.lib.drf.fields import ModelChoiceField

from happybudget.app.serializers import ModelSerializer
from happybudget.app.budgeting.fields import BudgetRelatedField
from happybudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)
from happybudget.app.tabling.serializers import row_order_serializer
from happybudget.app.tagging.serializers import ColorField

from .models import Fringe


class FringeSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    subaccounts = BudgetRelatedField(
        # The Budget will always be in context, regardless of whether or not
        # the request is a PATCH or a POST request.
        qs_filter=lambda c: lambda obj: obj.budget == c.budget,
        instance_cls=lambda c: {
            "budget": BudgetSubAccount,
            "template": TemplateSubAccount
        }[c.budget.domain],
        # We do not allow the SubAccount(s) associated with a Fringe to be
        # changed in a PATCH request, only a POST request.
        request_is_valid=lambda r, c:
        r.method == "POST" or c.get("bulk_create_context") is True,
        write_only=True,
        many=True
    )
    rate = serializers.FloatField(required=False, allow_null=True)
    cutoff = serializers.FloatField(required=False, allow_null=True)
    unit = ModelChoiceField(
        required=False,
        choices=Fringe.UNITS,
        allow_null=True
    )
    color = ColorField(
        content_type_model=Fringe,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Fringe
        fields = (
            'id', 'name', 'description', 'rate', 'cutoff', 'unit',
            'color', 'type', 'order', 'subaccounts')

    def create(self, validated_data, **kwargs):
        subaccounts = validated_data.pop('subaccounts', [])
        instance = super().create(validated_data, **kwargs)

        # After we create the Fringe, we must associate the provided subaccounts
        # with the Fringe we just created.
        for subaccount in subaccounts:
            assert subaccount.budget == instance.budget, \
                "SubAccount budget is not consistent with Fringe Budget.  " \
                "This should have been prevented via the serializer field."
            subaccount.fringes.add(instance)

        return instance


@row_order_serializer(table_filter=lambda d: {'budget_id': d.budget.id})
class FringeDetailSerializer(FringeSerializer):
    pass

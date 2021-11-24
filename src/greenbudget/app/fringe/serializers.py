from rest_framework import serializers

from greenbudget.lib.drf.fields import ModelChoiceField
from greenbudget.lib.drf.serializers import ModelSerializer

from greenbudget.app.tabling.serializers import row_order_serializer
from greenbudget.app.tagging.serializers import ColorField

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
            'color', 'type', 'order')


@row_order_serializer(table_filter=lambda d: {'budget_id': d['budget'].id})
class FringeDetailSerializer(FringeSerializer):
    pass

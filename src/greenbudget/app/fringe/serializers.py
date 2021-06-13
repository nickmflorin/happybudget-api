from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.fields import ModelChoiceField
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.tagging.serializers import ColorField

from .models import Fringe


class FringeSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
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
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    rate = serializers.FloatField(required=False, allow_null=True)
    cutoff = serializers.FloatField(required=False, allow_null=True)
    unit = ModelChoiceField(
        required=False,
        choices=Fringe.UNITS,
        allow_null=True
    )
    num_times_used = serializers.IntegerField(read_only=True)
    color = ColorField(
        content_type_model=Fringe,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Fringe
        fields = (
            'id', 'name', 'description', 'created_by', 'created_at',
            'updated_by', 'updated_at', 'rate', 'cutoff', 'unit',
            'num_times_used', 'color')

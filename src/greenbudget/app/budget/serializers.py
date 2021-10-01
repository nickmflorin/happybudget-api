from rest_framework import serializers, exceptions

from greenbudget.lib.drf.fields import (
    ModelChoiceField, Base64ImageField)
from greenbudget.lib.drf.serializers import ModelSerializer

from greenbudget.app.template.models import Template

from .models import BaseBudget, Budget


class BaseBudgetSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    type = serializers.CharField(read_only=True)

    class Meta:
        model = BaseBudget
        fields = ('id', 'name', 'type')


class BudgetSimpleSerializer(BaseBudgetSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    template = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        queryset=Template.objects.all(),
        allow_null=False
    )

    class Meta:
        model = Budget
        fields = BaseBudgetSerializer.Meta.fields + (
            'created_by', 'updated_at', 'created_at', 'template', 'image')

    def create(self, validated_data):
        if 'template' not in validated_data:
            return super().create(validated_data)
        template = validated_data.pop('template')
        if 'created_by' in validated_data:
            del validated_data['created_by']
        request = self.context['request']
        return template.derive(request.user, **validated_data)

    def validate_template(self, template):
        request = self.context['request']
        if not request.user.is_staff:
            if not template.created_by.is_staff \
                    and template.created_by != request.user:
                raise exceptions.ValidationError(
                    "Do not have permission to use template.")
        return template


class BudgetSerializer(BudgetSimpleSerializer):
    project_number = serializers.IntegerField(read_only=True)
    production_type = ModelChoiceField(
        choices=Budget.PRODUCTION_TYPES,
        required=False
    )
    shoot_date = serializers.DateTimeField(read_only=True)
    delivery_date = serializers.DateTimeField(read_only=True)
    build_days = serializers.IntegerField(read_only=True)
    prelight_days = serializers.IntegerField(read_only=True)
    studio_shoot_days = serializers.IntegerField(read_only=True)
    location_days = serializers.IntegerField(read_only=True)

    accumulated_value = serializers.FloatField(read_only=True)
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)

    class Meta:
        model = Budget
        fields = BudgetSimpleSerializer.Meta.fields \
            + Budget.CALCULATED_FIELDS \
            + (
                'project_number', 'production_type', 'shoot_date',
                'delivery_date', 'build_days', 'prelight_days',
                'studio_shoot_days', 'location_days', 'nominal_value'
            )

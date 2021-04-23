from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.fields import ModelChoiceField
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.common.serializers import EntitySerializer
from greenbudget.app.template.models import Template

from .models import BaseBudget, Budget


class TreeNodeSerializer(EntitySerializer):

    def get_children(self, instance):
        if instance.subaccounts.count():
            return self.__class__(instance.subaccounts.all(), many=True).data
        return []

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['children'] = self.get_children(instance)
        return rep


class BaseBudgetSimpleSerializer(EnhancedModelSerializer):
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


class BaseBudgetSerializer(BaseBudgetSimpleSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    trash = serializers.BooleanField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    image = serializers.ImageField(
        required=False,
        allow_empty_file=False
    )

    class Meta(BaseBudgetSimpleSerializer.Meta):
        model = BaseBudget
        fields = BaseBudgetSimpleSerializer.Meta.fields + (
            'created_by', 'created_at', 'updated_at', 'trash', 'estimated',
            'image')

    def validate_name(self, value):
        user = self.context['user']
        validator = serializers.UniqueTogetherValidator(
            queryset=self.Meta.model.objects.filter(created_by=user),
            fields=('name', ),
        )
        validator({'name': value, 'user': user}, self)
        return value


class BudgetSerializer(BaseBudgetSerializer):
    project_number = serializers.IntegerField(read_only=True)
    production_type = ModelChoiceField(
        choices=Budget.PRODUCTION_TYPES,
        required=False
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    shoot_date = serializers.DateTimeField(read_only=True)
    delivery_date = serializers.DateTimeField(read_only=True)
    build_days = serializers.IntegerField(read_only=True)
    prelight_days = serializers.IntegerField(read_only=True)
    studio_shoot_days = serializers.IntegerField(read_only=True)
    location_days = serializers.IntegerField(read_only=True)
    trash = serializers.BooleanField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    template = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        queryset=Template.objects.active(),
        allow_null=False
    )

    class Meta:
        model = Budget
        fields = BaseBudgetSerializer.Meta.fields + (
            'project_number', 'production_type', 'shoot_date', 'delivery_date',
            'build_days', 'prelight_days', 'studio_shoot_days', 'location_days',
            'actual', 'variance', 'template')

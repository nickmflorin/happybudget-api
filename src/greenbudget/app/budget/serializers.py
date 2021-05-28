from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.fields import (
    ModelChoiceField, Base64ImageField)
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.common.serializers import EntitySerializer
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.template.models import Template

from .models import BaseBudget, Budget


class TreeNodeSerializer(EntitySerializer):
    children = serializers.PrimaryKeyRelatedField(
        queryset=BudgetSubAccount.objects.all())

    def __init__(self, *args, **kwargs):
        # The subset is the set of SubAccount(s) that have been filtered by
        # the search.  Only these SubAccount(s) will be included as children
        # to each node of the tree.
        self._subset = kwargs.pop('subset')
        self._search_path = kwargs.pop('search_path')
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(
            in_search_path=instance in self._search_path,
            children=[
                self.__class__(child,
                    search_path=self._search_path, subset=self._subset).data
                for child in [
                    obj for obj in self._subset if obj.parent == instance]
            ]
        )
        return data


class BaseBudgetSerializer(EnhancedModelSerializer):
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
    image = Base64ImageField(required=False)
    template = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        queryset=Template.objects.active(),
        allow_null=False
    )

    class Meta:
        model = Budget
        fields = BaseBudgetSerializer.Meta.fields + (
            'created_by', 'updated_at', 'created_at', 'template', 'image')


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
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)

    class Meta:
        model = Budget
        fields = BudgetSimpleSerializer.Meta.fields + (
            'project_number', 'production_type', 'shoot_date', 'delivery_date',
            'build_days', 'prelight_days', 'studio_shoot_days', 'location_days',
            'actual', 'variance', 'estimated')

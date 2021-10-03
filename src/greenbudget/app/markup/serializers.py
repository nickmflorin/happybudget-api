from django.db import models
from rest_framework import serializers

from greenbudget.lib.drf.serializers import ModelSerializer
from greenbudget.lib.drf.fields import ModelChoiceField

from greenbudget.app.budgeting.fields import TableChildrenPrimaryKeyRelatedField
from greenbudget.app.budgeting.serializers import BudgetParentContextSerializer

from .models import Markup


class MarkupRemoveChildrenSerializer(ModelSerializer):
    children = TableChildrenPrimaryKeyRelatedField(
        many=True,
        obj_name='Markup',
        required=True,
        child_instance_cls=lambda parent: Markup.child_instance_cls_for_parent(
            parent),
        additional_instance_query=lambda parent, instance: models.Q(
            markups=instance
        ),
        error_message=(
            'The child {child_instance_name} with ID {pk_value} either does '
            'not exist, does not belong to the same parent '
            '({parent_instance_name} with ID {parent_pk_value}) as the '
            '{obj_name}, or is not a registered child of {obj_name}.'
        )
    )

    class Meta:
        model = Markup
        fields = ('children', )

    def update(self, instance, validated_data):
        instance.remove_children(*validated_data['children'])
        return instance


class MarkupAddChildrenSerializer(ModelSerializer):
    children = TableChildrenPrimaryKeyRelatedField(
        obj_name='Markup',
        many=True,
        required=True,
        child_instance_cls=lambda parent: Markup.child_instance_cls_for_parent(
            parent),
        exclude_instance_query=lambda parent, instance: models.Q(
            pk__in=[
                obj[0]
                for obj in list(instance.children.only('pk').values_list('pk'))
            ]
        ),
        error_message=(
            'The child {child_instance_name} with ID {pk_value} either does '
            'not exist, does not belong to the same parent '
            '({parent_instance_name} with ID {parent_pk_value}) as the '
            '{obj_name}, or is already a registered child of {obj_name}.'
        )
    )

    class Meta:
        model = Markup
        fields = ('children',)

    def update(self, instance, validated_data):
        instance.add_children(*validated_data['children'])
        return instance


class MarkupSimpleSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    identifier = serializers.CharField(
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

    class Meta:
        model = Markup
        fields = ('id', 'identifier', 'description', 'type')


class MarkupSerializer(BudgetParentContextSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    identifier = serializers.CharField(
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
    actual = serializers.FloatField(read_only=True)
    unit = ModelChoiceField(
        required=False,
        choices=Markup.UNITS,
        allow_null=True
    )
    children = TableChildrenPrimaryKeyRelatedField(
        obj_name='Markup',
        many=True,
        required=False,
        child_instance_cls=lambda parent: Markup.child_instance_cls_for_parent(
            parent)
    )

    class Meta:
        model = Markup
        fields = (
            'id', 'identifier', 'description', 'created_by', 'created_at',
            'updated_by', 'updated_at', 'rate', 'unit', 'children', 'type',
            'actual')

    def create(self, validated_data, **kwargs):
        children = validated_data.pop('children', None)
        instance = super().create(validated_data, **kwargs)

        if children is not None:
            instance.set_children(children)

        return instance

    def update(self, instance, validated_data, **kwargs):
        children = validated_data.pop('children', None)
        instance = super().update(instance, validated_data, **kwargs)

        if children is not None:
            instance.set_children(children)

        return instance

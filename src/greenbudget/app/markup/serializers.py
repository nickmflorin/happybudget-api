from django.db import models
from rest_framework import serializers

from greenbudget.lib.drf.exceptions import InvalidFieldError
from greenbudget.lib.drf.fields import ModelChoiceField
from greenbudget.lib.drf.serializers import ModelSerializer

from greenbudget.app.budgeting.serializers import BudgetParentContextSerializer
from greenbudget.app.tabling.fields import TableChildrenPrimaryKeyRelatedField

from .models import Markup


class MarkupRemoveChildrenSerializer(ModelSerializer):
    children = TableChildrenPrimaryKeyRelatedField(
        many=True,
        obj_name='Markup',
        required=True,
        child_instance_cls=lambda parent: parent.child_instance_cls,
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

    def validate(self, attrs):
        if self.instance.unit != Markup.UNITS.percent:
            raise InvalidFieldError('children', message=(
                "Markup must have unit `percent` to modify its children."))
        return attrs

    def update(self, instance, validated_data):
        instance.remove_children(*validated_data['children'])
        return instance


class MarkupAddChildrenSerializer(ModelSerializer):
    children = TableChildrenPrimaryKeyRelatedField(
        obj_name='Markup',
        many=True,
        required=True,
        child_instance_cls=lambda parent: parent.child_instance_cls,
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

    def validate(self, attrs):
        if self.instance.unit != Markup.UNITS.percent:
            raise InvalidFieldError('children', message=(
                "Markup must have unit `percent` to modify its children."))
        return attrs

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
    rate = serializers.FloatField(required=False, allow_null=True)
    actual = serializers.FloatField(read_only=True)
    unit = ModelChoiceField(
        required=True,
        choices=Markup.UNITS,
        allow_null=False,
    )
    children = TableChildrenPrimaryKeyRelatedField(
        obj_name='Markup',
        many=True,
        required=False,
        child_instance_cls=lambda parent: parent.child_instance_cls,
    )

    class Meta:
        model = Markup
        fields = (
            'id', 'identifier', 'description', 'rate', 'unit', 'children',
            'type', 'actual')

    def validate(self, attrs):
        # If creating a new instance (via POST) the unit will always be in the
        # data.  Otherwise, the unit is either in the data (via PATCH) or we use
        # the value of the current instance being updated.
        if self.instance is None:
            unit = attrs['unit']
        else:
            # Be careful here with incorrect falsey values for `unit` (which
            # can have value of 0).
            unit = getattr(self.instance, 'unit')
            if 'unit' in attrs:
                unit = attrs['unit']

        if unit == Markup.UNITS.flat:
            # If the Markup is being changed from unit PERCENT to FLAT, the
            # children will either not be in the payload or will be an empty
            # list - and we do not want to include it in the validated data
            # because the signals will take care of removing them.
            children = attrs.pop('children', [])
            if len(children) != 0:
                raise InvalidFieldError('children', message=(
                    'A markup with unit `flat` cannot have children.'))
            return attrs
        else:
            # If the Markup is being created, and the unit is PERCENT, the
            # children must be in the payload and must be non-empty.
            if self.instance is None:
                if 'children' not in attrs or len(attrs['children']) == 0:
                    raise InvalidFieldError('children', message=(
                        'A markup with unit `percent` must have at least 1 '
                        'child.'
                    ))
            else:
                # If the Markup is being changed from unit FLAT to PERCENT, the
                # Markup *should not* already have children, and providing the
                # children in the payload is required.
                children = attrs.get(
                    'children', getattr(self.instance, 'children'))
                if len(children) == 0 and unit == Markup.UNITS.percent:
                    raise InvalidFieldError('children', message=(
                        'A markup with unit `percent` must have at least 1 '
                        'child.'
                    ))

        return attrs

    def create(self, validated_data, **kwargs):
        children = validated_data.pop('children', None)
        instance = super().create(validated_data, **kwargs)

        if children is not None and instance.unit == Markup.UNITS.percent:
            # If the instance is being changed to unit FLAT, the children will
            # be removed by the signals.
            assert len(children) != 0, \
                "A Markup with unit PERCENT should always have children."
            instance.set_children(children)
        return instance

    def update(self, instance, validated_data, **kwargs):
        children = validated_data.pop('children', None)
        instance = super().update(instance, validated_data, **kwargs)

        if children is not None and instance.unit == Markup.UNITS.percent:
            assert len(children) != 0, \
                "A Markup with unit PERCENT should always have children."
            instance.set_children(children)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.unit == Markup.UNITS.flat:
            if self._only_model or self.read_only is True or 'children' in data:
                del data['children']
            else:
                del data['data']['children']
        return data

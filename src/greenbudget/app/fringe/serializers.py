from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.fields import ModelChoiceField
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.budget.models import BaseBudget
from greenbudget.app.common.serializers import AbstractBulkUpdateSerializer

from .models import Fringe


class FringeSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True
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

    class Meta:
        model = Fringe
        fields = (
            'id', 'name', 'description', 'created_by', 'created_at',
            'updated_by', 'updated_at', 'rate', 'cutoff', 'unit',
            'num_times_used')

    def validate_name(self, value):
        # In the case that the serializer is nested and being used in a write
        # context, we do not have access to the context.  Validation will
        # have to be done by the serializer using this serializer in its nested
        # form.
        if self._nested is not True:
            budget = self.context.get('budget')
            if budget is None:
                budget = self.instance.budget
            validator = serializers.UniqueTogetherValidator(
                queryset=budget.fringes.all(),
                fields=('name', ),
            )
            validator({'name': value}, self)
        return value


class FringeBulkChangeSerializer(FringeSerializer):
    id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Fringe.objects.all()
    )

    def validate_id(self, instance):
        budget = self.parent.parent.instance
        if budget != instance.budget:
            raise exceptions.ValidationError(
                "The fringe %s does not belong to budget %s."
                % (instance.pk, budget.pk)
            )
        return instance


class BulkCreateFringesSerializer(serializers.ModelSerializer):
    data = FringeSerializer(many=True, nested=True)

    class Meta:
        model = BaseBudget
        fields = ('data', )

    def update(self, instance, validated_data):
        fringes = []
        for payload in validated_data['data']:
            serializer = FringeSerializer(data=payload, context={
                'budget': instance
            })
            serializer.is_valid(raise_exception=True)
            # Note that the updated_by argument is the user updating the
            # Budget by adding new Fringe(s), so the Fringe(s) should
            # be denoted as having been created by this user.
            fringe = serializer.save(
                updated_by=validated_data['updated_by'],
                created_by=validated_data['updated_by'],
                budget=instance
            )
            fringes.append(fringe)
        return fringes


class BulkUpdateFringesSerializer(AbstractBulkUpdateSerializer):
    data = FringeBulkChangeSerializer(many=True, nested=True)

    class Meta:
        model = BaseBudget
        fields = ('data', )

    def update(self, instance, validated_data):
        for fringe, change in validated_data['data']:
            serializer = FringeSerializer(
                instance=fringe,
                data=change,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=validated_data['updated_by'])
        return instance

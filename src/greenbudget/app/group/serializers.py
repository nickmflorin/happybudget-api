from rest_framework import serializers

from greenbudget.lib.drf.serializers import ModelSerializer

from greenbudget.app.budgeting.fields import TableChildrenPrimaryKeyRelatedField
from greenbudget.app.markup.models import Markup
from greenbudget.app.tagging.serializers import ColorField

from .models import Group


class GroupSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    color = ColorField(content_type_model=Group, required=False)
    actual = serializers.FloatField(read_only=True)
    children = TableChildrenPrimaryKeyRelatedField(
        obj_name='Group',
        many=True,
        required=False,
        child_instance_cls=lambda parent: Group.child_instance_cls_for_parent(
            parent)
    )
    children_markups = TableChildrenPrimaryKeyRelatedField(
        obj_name='Group',
        many=True,
        required=False,
        child_instance_cls=Markup
    )

    class Meta:
        model = Group
        fields = (
            'id', 'name', 'created_by', 'created_at', 'updated_by',
            'updated_at', 'color', 'estimated', 'children', 'actual',
            'type', 'children_markups')

    def create(self, validated_data, **kwargs):
        children = validated_data.pop('children', [])
        instance = super().create(validated_data, **kwargs)

        # After we create the Group, we must associate the provided children
        # with the Group we just created.
        for child in children:
            child.group = instance
            child.save(update_fields=['group'])

        return instance

    def update(self, instance, validated_data, **kwargs):
        children = validated_data.pop('children', [])
        instance = super().update(instance, validated_data, **kwargs)

        # After we update the Group, we must associate the provided children
        # with the Group we just updated.
        for child in children:
            child.group = instance
            child.save(update_fields=['group'])

        return instance

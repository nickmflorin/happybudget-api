from rest_framework import serializers, exceptions

from greenbudget.lib.drf.serializers import ModelSerializer

from greenbudget.app.tabling.fields import TableChildrenPrimaryKeyRelatedField
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
    color = ColorField(content_type_model=Group, required=False)
    children = TableChildrenPrimaryKeyRelatedField(
        obj_name='Group',
        many=True,
        required=True,
        child_instance_cls=lambda parent: parent.child_instance_cls,
    )

    class Meta:
        model = Group
        fields = ('id', 'name', 'color', 'children', 'type')

    def validate_children(self, children):
        if len(children) == 0:
            raise exceptions.ValidationError(
                "A group must have at least 1 child.")
        return children

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

        # We have to both remove children that are not included in the payload
        # and add the children that are included in the payload.
        for child in instance.children.all():
            if child not in children:
                child.group = None
                child.save(update_fields=["group"])

        # After we update the Group, we must associate the provided children
        # with the Group we just updated.
        for child in children:
            if child not in instance.children.all():
                child.group = instance
                child.save(update_fields=['group'])

        return instance

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from greenbudget.app import exceptions

from greenbudget.app.budget.models import BaseBudget
from greenbudget.app.tabling.fields import TablePrimaryKeyRelatedField
from greenbudget.app.tagging.serializers import ColorField

from .models import Group


def group_table_filter(ctx):
    # If the Group contains Account(s), then it's parent is a Budget and the
    # table is indexed by the parent ID.  If the Group contains SubAccount(s),
    # then it's parent is an Account and the table is indexed by the generic
    # object_id and content_type_id.
    if isinstance(ctx.parent, BaseBudget):
        return {'parent_id': ctx.parent.id}
    return {
        'object_id': ctx.parent.id,
        'content_type_id': ContentType.objects.get_for_model(
            type(ctx.parent)).id,
    }


class GroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    color = ColorField(
        content_type_model=Group,
        required=False,
        allow_null=True,
    )
    children = TablePrimaryKeyRelatedField(
        table_filter=group_table_filter,
        many=True,
        required=True,
        table_instance_cls=lambda c: c.parent.child_instance_cls,
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

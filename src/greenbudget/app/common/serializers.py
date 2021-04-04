import functools
from rest_framework import serializers


def flexible_getter(field):
    def decorator(func):
        @functools.wraps(func)
        def method(serializer, instance):
            if hasattr(instance, field):
                return getattr(instance, field)
            return None
        return method
    return decorator


class EntitySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    type = serializers.CharField(read_only=True)
    description = serializers.SerializerMethodField()

    @flexible_getter('description')
    def get_description(self, instance):
        pass

    @flexible_getter('name')
    def get_name(self, instance):
        pass

    @flexible_getter('identifier')
    def get_identifier(self, instance):
        pass


class AbstractBulkUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        abstract = True

    def validate_data(self, data):
        grouped = {}
        for change in data:
            instance = change['id']
            del change['id']
            if instance.pk not in grouped:
                grouped[instance.pk] = {
                    'instance': instance,
                    'change': change,
                }
            else:
                grouped[instance.pk] = {
                    'instance': grouped[instance.pk]['instance'],
                    'change': {**grouped[instance.pk]['change'], **change},
                }
        return [(gp['instance'], gp['change']) for _, gp in grouped.items()]

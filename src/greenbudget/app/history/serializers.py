from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from greenbudget.app.budget_item.serializers import BudgetItemSerializer
from greenbudget.app.user.serializers import SimpleUserSerializer

from .models import Event, FieldAlterationEvent, CreateEvent


class EventSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    user = SimpleUserSerializer(read_only=True)
    # Note: The BudgetItemSerializer is Polymorphic wrt Account/SubAccount.
    # It will still work for Actual - but will omit the `identifier` field.
    # This is kind of a hacky way to do this, and should be resolved with a
    # separate dedicated serializer in the future.
    content_object = BudgetItemSerializer(read_only=True)

    class Meta:
        model = FieldAlterationEvent
        fields = (
            'id', 'created_at', 'user', 'content_object')


class CreateEventSerializer(EventSerializer):
    pass


class FieldAlterationEventSerializer(EventSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    new_value = serializers.JSONField(read_only=True)
    old_value = serializers.JSONField(read_only=True)
    field = serializers.CharField(read_only=True)

    class Meta:
        model = FieldAlterationEvent
        fields = EventSerializer.Meta.fields + (
            'new_value', 'old_value', 'field')


class EventPolymorphicSerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'

    model_serializer_mapping = {
        Event: EventSerializer,
        FieldAlterationEvent: FieldAlterationEventSerializer,
        CreateEvent: CreateEventSerializer
    }

    def to_resource_type(self, model_or_instance):
        return model_or_instance.type

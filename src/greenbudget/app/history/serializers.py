from generic_relations.relations import GenericRelatedField

from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.serializers import AccountSimpleSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.serializers import SubAccountSimpleSerializer
from greenbudget.app.user.serializers import SimpleUserSerializer

from .models import Event, FieldAlterationEvent, CreateEvent


class EventSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    user = SimpleUserSerializer(read_only=True)
    content_object = GenericRelatedField({
        BudgetAccount: AccountSimpleSerializer(),
        BudgetSubAccount: SubAccountSimpleSerializer()
    })

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

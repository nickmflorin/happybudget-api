from rest_framework import serializers

from greenbudget.app.user.serializers import SimpleUserSerializer

from .models import FieldAlterationEvent


class FieldAlterationEventSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    new_value = serializers.JSONField(read_only=True)
    old_value = serializers.JSONField(read_only=True)
    field = serializers.CharField(read_only=True)
    content_object_type = serializers.ChoiceField(
        read_only=True,
        choices=["actual", "account", "subaccount"]
    )
    object_id = serializers.IntegerField(read_only=True)
    user = SimpleUserSerializer(read_only=True)
    type = serializers.ChoiceField(
        read_only=True,
        choices=["field_alteration"]
    )

    class Meta:
        model = FieldAlterationEvent
        fields = (
            'id', 'created_at', 'new_value', 'old_value', 'field', 'object_id',
            'content_object_type', 'user', 'type')

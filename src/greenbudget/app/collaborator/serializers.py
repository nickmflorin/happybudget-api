from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from greenbudget.lib.drf.fields import ModelChoiceField
from greenbudget.lib.drf.validators import UniqueTogetherValidator

from greenbudget.app.user.models import User
from greenbudget.app.user.serializers import SimpleUserSerializer

from .models import Collaborator


class CollaboratorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.standard_filter(),
        required=True
    )
    access_type = ModelChoiceField(
        required=False,
        choices=Collaborator.ACCESS_TYPES,
        allow_null=False
    )

    class Meta:
        model = Collaborator
        fields = ('id', 'type', 'created_at', 'access_type', 'user')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context['request'].method == 'PATCH':
            self.fields['user'] = SimpleUserSerializer(read_only=True)

    def validate(self, attrs):
        # We only have to worry about POST requests, since we cannot change
        # the user via a PATCH request.
        if self.instance is None:
            assert 'budget' in self.context, \
                "The budget must be provided in context when using this " \
                "serializer in a POST request context."
            validator = UniqueTogetherValidator(
                queryset=Collaborator.objects.all(),
                context_fields=(
                    ('object_id', lambda c: c['budget'].pk),
                    ('content_type', lambda c:
                        ContentType.objects.get_for_model(type(c['budget'])))
                ),
                fields=('user',),
                message="The user is already a collaborator.",
                exception_fields='user'
            )
            validator(attrs, self)
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = SimpleUserSerializer(instance.user).data
        return data

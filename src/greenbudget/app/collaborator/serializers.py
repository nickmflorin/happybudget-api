from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from greenbudget.lib.drf.fields import ModelChoiceField
from greenbudget.lib.drf.validators import UniqueTogetherValidator

from greenbudget.app import exceptions
from greenbudget.app.serializers import ModelSerializer
from greenbudget.app.user.serializers import SimpleUserSerializer

from .fields import CollaboratingUserField
from .models import Collaborator


class CollaboratorSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    user = CollaboratingUserField(required=True)
    access_type = ModelChoiceField(
        required=False,
        choices=Collaborator.ACCESS_TYPES,
        allow_null=False
    )

    class Meta:
        model = Collaborator
        fields = (
            'id', 'type', 'created_at', 'updated_at', 'access_type', 'user')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.request.method == 'PATCH':
            self.fields['user'] = SimpleUserSerializer(read_only=True)

    def validate(self, attrs):
        if self.instance is None:
            # This might change in the future, but for now users can only be
            # added as a collaborator by another user.  This check should be
            # performed by the CollaboratingUserField field.
            assert self.user != attrs['user']

            assert 'budget' in self.context, \
                "The budget must be provided in context when using this " \
                "serializer in a POST request context."

            # We only have to worry about ensuring user/instance uniqueness
            # on POST requests, since we cannot change the user via a PATCH
            # request.
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
        elif self.user == self.instance.user:
            raise exceptions.BadRequest(
                "A user cannot update their own collaboration state.")
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = SimpleUserSerializer(instance.user).data
        return data

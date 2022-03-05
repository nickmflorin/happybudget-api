from rest_framework import serializers

from .client import client


class CreateLinkTokenSerializer(serializers.Serializer):
    link_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        return {"link_token": client.create_link_token(
            user=self.context["user"],
            raise_exception=True
        )}

    def create(self, validated_data):
        return validated_data

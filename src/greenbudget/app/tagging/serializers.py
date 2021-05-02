from rest_framework import serializers

from .models import Color


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color

    def to_representation(self, instance):
        return instance.code

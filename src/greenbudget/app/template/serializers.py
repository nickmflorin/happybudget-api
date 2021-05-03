from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.fields import Base64ImageField

from greenbudget.app.budget.serializers import BaseBudgetSerializer
from .models import Template


class TemplateSimpleSerializer(BaseBudgetSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Template
        fields = BaseBudgetSerializer.Meta.fields + (
            'created_by', 'updated_at', 'created_at', 'image')


class TemplateSerializer(TemplateSimpleSerializer):
    community = serializers.BooleanField(
        required=False,
        write_only=True
    )
    estimated = serializers.FloatField(read_only=True)

    class Meta:
        model = Template
        fields = TemplateSimpleSerializer.Meta.fields + (
            'community', 'estimated')

    def validate(self, attrs):
        request = self.context["request"]
        if self.instance is not None and self.instance.community is True \
                and not request.user.is_staff:
            raise exceptions.PermissionDenied(
                "Only staff users can modify community templates."
            )
        elif attrs.get("community", False) is True \
                and not request.user.is_staff:
            raise exceptions.PermissionDenied(
                "Only staff users can modify community templates."
            )
        return super().validate(attrs)

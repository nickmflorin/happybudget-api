from rest_framework import serializers, exceptions

from greenbudget.app.budget.serializers import BaseBudgetSerializer
from .models import Template


class TemplateSerializer(BaseBudgetSerializer):
    community = serializers.BooleanField(
        required=False,
        write_only=True
    )

    class Meta:
        model = Template
        fields = BaseBudgetSerializer.Meta.fields + ('community', )

    def validate(self, attrs):
        request = self.context["request"]
        if "community" in attrs and not request.user.is_staff:
            raise exceptions.PermissionDenied(
                "Only staff users can modify community templates."
            )
        return super().validate(attrs)

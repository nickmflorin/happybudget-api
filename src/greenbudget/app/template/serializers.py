from rest_framework import serializers, exceptions

from greenbudget.lib.drf.exceptions import InvalidFieldError
from greenbudget.lib.drf.fields import Base64ImageField

from greenbudget.app.budget.serializers import BaseBudgetSerializer
from .models import Template


class TemplateSimpleSerializer(BaseBudgetSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    hidden = serializers.BooleanField(read_only=True)

    class Meta:
        model = Template
        fields = BaseBudgetSerializer.Meta.fields + (
            'created_by', 'updated_at', 'created_at', 'image', 'hidden')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.community is False:
            del data['hidden']
        return data


class TemplateSerializer(TemplateSimpleSerializer):
    community = serializers.BooleanField(required=False, write_only=True)
    hidden = serializers.BooleanField(required=False)

    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)

    class Meta:
        model = Template
        fields = TemplateSimpleSerializer.Meta.fields \
            + (
                'nominal_value',
                'actual',
                'accumulated_markup_contribution',
                'accumulated_fringe_contribution'
            ) \
            + ('community', 'hidden', 'nominal_value')

    def validate(self, attrs):
        request = self.context["request"]
        if request.method == "POST":
            # For POST requests to /templates/community, the community flag is
            # automatically set to True and for POST requests to /templates, the
            # community flag is automatically set to False.
            community_endpoint = self.context.get('community', False)
            attrs['community'] = community_endpoint
            if attrs.get('hidden', False) and attrs['community'] is False:
                raise InvalidFieldError("hidden",
                    message="Only community templates can be hidden/shown.")
        else:
            is_community = attrs.get("community", self.instance.community)
            if not request.user.is_staff and is_community:
                raise exceptions.PermissionDenied(
                    "Only staff users can modify community templates.")
            elif 'hidden' in attrs:
                if not is_community:
                    raise InvalidFieldError("hidden",
                        message="Only community templates can be hidden/shown.")

        return super().validate(attrs)

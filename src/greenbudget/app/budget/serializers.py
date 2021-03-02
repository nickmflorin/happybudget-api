from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)
from greenbudget.app.user.serializers import UserSerializer

from .models import Budget


class BudgetSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    author = UserSerializer(nested=True, read_only=True)
    project_number = serializers.IntegerField(read_only=True)
    production_type = serializers.ChoiceField(choices=Budget.PRODUCTION_TYPES)
    production_type_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    shoot_date = serializers.DateTimeField(read_only=True)
    delivery_date = serializers.DateTimeField(read_only=True)
    build_days = serializers.IntegerField(read_only=True)
    prelight_days = serializers.IntegerField(read_only=True)
    studio_shoot_days = serializers.IntegerField(read_only=True)
    location_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = Budget
        fields = (
            'id', 'name', 'author', 'project_number', 'production_type',
            'production_type_name', 'created_at', 'shoot_date',
            'delivery_date', 'build_days', 'prelight_days', 'studio_shoot_days',
            'location_days')

    def validate_name(self, value):
        user = self.context['user']
        validator = serializers.UniqueTogetherValidator(
            queryset=Budget.objects.filter(author=user),
            fields=('name', ),
        )
        validator({'name': value, 'user': user}, self)
        return value

from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)
from greenbudget.app.account.models import Account
from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.user.serializers import UserSerializer

from .models import Budget


class BudgetElementSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)

    def get_type(self, instance):
        if isinstance(instance, Account):
            return "account"
        assert isinstance(instance, SubAccount)
        return "subaccount"

    def get_name(self, instance):
        if isinstance(instance, Account):
            return instance.account_number
        assert isinstance(instance, SubAccount)
        return instance.name


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
    updated_at = serializers.DateTimeField(read_only=True)
    shoot_date = serializers.DateTimeField(read_only=True)
    delivery_date = serializers.DateTimeField(read_only=True)
    build_days = serializers.IntegerField(read_only=True)
    prelight_days = serializers.IntegerField(read_only=True)
    studio_shoot_days = serializers.IntegerField(read_only=True)
    location_days = serializers.IntegerField(read_only=True)
    trash = serializers.BooleanField(read_only=True)
    estimated = serializers.DecimalField(
        read_only=True,
        decimal_places=2,
        max_digits=10
    )
    actual = serializers.DecimalField(
        read_only=True,
        decimal_places=2,
        max_digits=10
    )
    variance = serializers.DecimalField(
        read_only=True,
        decimal_places=2,
        max_digits=10
    )

    class Meta:
        model = Budget
        fields = (
            'id', 'name', 'author', 'project_number', 'production_type',
            'production_type_name', 'created_at', 'shoot_date',
            'delivery_date', 'build_days', 'prelight_days', 'studio_shoot_days',
            'location_days', 'updated_at', 'trash', 'estimated', 'actual',
            'variance')

    def validate_name(self, value):
        user = self.context['user']
        validator = serializers.UniqueTogetherValidator(
            queryset=Budget.objects.filter(author=user),
            fields=('name', ),
        )
        validator({'name': value, 'user': user}, self)
        return value

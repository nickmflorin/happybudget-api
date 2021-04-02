from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.account.serializers import (
    AccountSerializer, AccountBulkChangeSerializer)
from greenbudget.app.actual.serializers import (
    ActualSerializer, ActualBulkChangeSerializer)

from .models import Budget


class BudgetSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
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
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)

    class Meta:
        model = Budget
        fields = (
            'id', 'name', 'created_by', 'project_number', 'production_type',
            'production_type_name', 'created_at', 'shoot_date',
            'delivery_date', 'build_days', 'prelight_days', 'studio_shoot_days',
            'location_days', 'updated_at', 'trash', 'estimated', 'actual',
            'variance')

    def validate_name(self, value):
        user = self.context['user']
        validator = serializers.UniqueTogetherValidator(
            queryset=Budget.objects.filter(created_by=user),
            fields=('name', ),
        )
        validator({'name': value, 'user': user}, self)
        return value


class BudgetBulkCreateAccountsSerializer(serializers.ModelSerializer):
    data = AccountSerializer(many=True, nested=True)

    class Meta:
        model = Budget
        fields = ('data', )

    def update(self, instance, validated_data):
        accounts = []
        for payload in validated_data['data']:
            serializer = AccountSerializer(data=payload, context={
                'budget': instance
            })
            serializer.is_valid(raise_exception=True)
            # Note that the updated_by argument is the user updating the
            # Budget by adding new Account(s), so the Account(s) should
            # be denoted as having been created by this user.
            account = serializer.save(
                updated_by=validated_data['updated_by'],
                created_by=validated_data['updated_by'],
                budget=instance
            )
            accounts.append(account)
        return accounts


class BudgetBulkUpdateAccountsSerializer(serializers.ModelSerializer):
    data = AccountBulkChangeSerializer(many=True, nested=True)

    class Meta:
        model = Budget
        fields = ('data', )

    def validate_data(self, data):
        grouped = {}
        for change in data:
            instance = change['id']
            del change['id']
            if instance.pk not in grouped:
                grouped[instance.pk] = {
                    **{'instance': instance}, **change}
            else:
                grouped[instance.pk] = {
                    **grouped[instance.pk],
                    **{'instance': instance},
                    **change
                }
        return grouped

    def update(self, instance, validated_data):
        for id, change in validated_data['data'].items():
            account = change['instance']
            del change['instance']
            serializer = AccountSerializer(
                instance=account,
                data=change,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=validated_data['updated_by'])
        return instance


class BudgetBulkUpdateActualsSerializer(serializers.ModelSerializer):
    data = ActualBulkChangeSerializer(many=True, nested=True)

    class Meta:
        model = Budget
        fields = ('data', )

    def validate_data(self, data):
        grouped = {}
        for change in data:
            instance = change['id']
            del change['id']
            if instance.pk not in grouped:
                grouped[instance.pk] = {
                    **{'instance': instance}, **change}
            else:
                grouped[instance.pk] = {
                    **grouped[instance.pk],
                    **{'instance': instance},
                    **change
                }
        return grouped

    def update(self, instance, validated_data):
        for id, change in validated_data['data'].items():
            account = change['instance']
            del change['instance']
            serializer = ActualSerializer(
                instance=account,
                data=change,
                partial=True,
                context={'request': self.context['request']}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=validated_data['updated_by'])
        return instance

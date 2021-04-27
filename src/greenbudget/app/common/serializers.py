from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    PolymorphicNonPolymorphicSerializer)

from greenbudget.app.account.models import Account
from greenbudget.app.budget.models import Budget
from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.template.models import Template


class EntitySerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        Account: (
            "greenbudget.app.account.serializers.AccountSimpleSerializer",
            "account"
        ),
        SubAccount: (
            "greenbudget.app.subaccount.serializers.SubAccountSimpleSerializer",
            "subaccount"
        ),
        Budget: (
            "greenbudget.app.budget.serializers.BaseBudgetSimpleSerializer",
            "budget"
        ),
        Template: (
            "greenbudget.app.budget.serializers.BaseBudgetSimpleSerializer",
            "template"
        )
    }


def create_bulk_create_serializer(data_serializer):
    class AbstractBulkCreateSerializer(serializers.ModelSerializer):
        data = data_serializer(many=True, nested=True, required=False)
        count = serializers.IntegerField(required=False)

        class Meta:
            abstract = True
            fields = ('data', 'count')

        def validate(self, attrs):
            if 'data' not in attrs and 'count' not in attrs:
                raise exceptions.ValidationError(
                    "Either the `data` or `count` parameters must be provided."
                )
            return attrs

        def perform_save(self, serializer, instance, validated_data):
            raise NotImplementedError()

        def get_serializer_context(self, instance):
            raise NotImplementedError()

        def update(self, instance, validated_data):
            models = []
            context = self.get_serializer_context(instance)
            if 'data' in validated_data:
                for payload in validated_data['data']:
                    serializer = data_serializer(data=payload, context=context)
                    serializer.is_valid(raise_exception=True)
                    model = self.perform_save(
                        serializer, instance, validated_data)
                    models.append(model)
            else:
                for _ in range(validated_data['count']):
                    serializer = data_serializer(data={}, context=context)
                    serializer.is_valid(raise_exception=True)
                    model = self.perform_save(
                        serializer, instance, validated_data)
                    models.append(model)
            return models
    return AbstractBulkCreateSerializer


class AbstractBulkUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        abstract = True

    def validate_data(self, data):
        grouped = {}
        for change in data:
            instance = change['id']
            del change['id']
            if instance.pk not in grouped:
                grouped[instance.pk] = {
                    'instance': instance,
                    'change': change,
                }
            else:
                grouped[instance.pk] = {
                    'instance': grouped[instance.pk]['instance'],
                    'change': {**grouped[instance.pk]['change'], **change},
                }
        return [(gp['instance'], gp['change']) for _, gp in grouped.items()]

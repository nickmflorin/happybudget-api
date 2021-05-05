from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.fields import ModelChoiceField
from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.budget.models import BaseBudget
from greenbudget.app.common.serializers import (
    EntitySerializer,
    AbstractBulkUpdateSerializer,
    create_bulk_create_serializer
)
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import (
    BudgetSubAccountGroup,
    TemplateSubAccountGroup
)

from .models import SubAccount, BudgetSubAccount, TemplateSubAccount


class SubAccountSimpleSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    identifier = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False,
        trim_whitespace=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=False,
        trim_whitespace=False
    )
    name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=False,
        trim_whitespace=False
    )

    class Meta:
        model = SubAccount
        fields = ('id', 'name', 'identifier', 'type', 'description')


class SubAccountSerializer(SubAccountSimpleSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    quantity = serializers.IntegerField(
        required=False,
        allow_null=True
    )
    rate = serializers.FloatField(required=False, allow_null=True)
    multiplier = serializers.FloatField(required=False, allow_null=True)
    estimated = serializers.FloatField(read_only=True)
    unit = ModelChoiceField(
        required=False,
        choices=SubAccount.UNITS,
        allow_null=True
    )
    budget = serializers.PrimaryKeyRelatedField(read_only=True)
    subaccounts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)
    account = serializers.IntegerField(read_only=True, source='account.pk')
    object_id = serializers.IntegerField(read_only=True)
    parent_type = serializers.ChoiceField(
        choices=["account", "subaccount"],
        read_only=True
    )
    fringes = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Fringe.objects.filter(budget__trash=False)
    )

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + (
            'identifier', 'name', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'quantity', 'rate', 'multiplier', 'unit', 'account',
            'object_id', 'parent_type', 'ancestors', 'estimated', 'subaccounts',
            'budget', 'siblings', 'fringes')

    def validate(self, attrs):
        if self.instance is not None and self.instance.subaccounts.count() != 0:
            if any([field in attrs for field in self.instance.DERIVING_FIELDS]):
                raise exceptions.ValidationError(
                    "Field can only be updated when the sub account is not "
                    "derived."
                )
        return super().validate(attrs)


class BudgetSubAccountSerializer(SubAccountSerializer):
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    group = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=BudgetSubAccountGroup.objects.all()
    )

    class Meta:
        model = BudgetSubAccount
        fields = SubAccountSerializer.Meta.fields + (
            'actual', 'variance', 'group')


class TemplateSubAccountSerializer(SubAccountSerializer):
    group = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=TemplateSubAccountGroup.objects.all()
    )

    class Meta:
        model = TemplateSubAccount
        fields = SubAccountSerializer.Meta.fields + ('group', )


def create_bulk_create_subaccounts_serializer(model_cls):
    data_serializer = BudgetSubAccountSerializer
    if model_cls is TemplateSubAccount:
        data_serializer = TemplateSubAccountSerializer

    base_serializer = create_bulk_create_serializer(data_serializer)

    class BulkCreateSubAccountsSerializer(base_serializer):

        class Meta(base_serializer.Meta):
            model = BaseBudget

        def get_serializer_context(self, instance):
            return {'parent': instance}

        def perform_save(self, serializer, instance, validated_data):
            # Note that the updated_by argument is the user updating the
            # Account by adding new SubAccount(s), so the SubAccount(s)
            # should be denoted as having been created by this user.
            return serializer.save(
                updated_by=validated_data['updated_by'],
                created_by=validated_data['updated_by'],
                object_id=instance.pk,
                content_type=ContentType.objects.get_for_model(model_cls),
                parent=instance,
                budget=instance.budget
            )

    return BulkCreateSubAccountsSerializer


def create_subaccount_bulk_change_serializer(model_cls):
    base_serializer = BudgetSubAccountSerializer
    if model_cls is TemplateSubAccount:
        base_serializer = TemplateSubAccountSerializer

    class SubAccountBulkChangeSerializer(base_serializer):
        id = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=model_cls.objects.all()
        )

        def validate_id(self, instance):
            account = self.parent.parent.instance
            if account != instance.parent:
                raise exceptions.ValidationError(
                    "The sub-account %s does not belong to account %s."
                    % (instance.pk, account.pk)
                )
            return instance
    return SubAccountBulkChangeSerializer


def create_bulk_update_subaccounts_serializer(model_cls):
    class BulkUpdateSubAccountsSerializer(AbstractBulkUpdateSerializer):
        data = create_subaccount_bulk_change_serializer(model_cls)(
            many=True, nested=True)

        class Meta:
            model = BaseBudget
            fields = ('data', )

        def update(self, instance, validated_data):
            for subaccount, change in validated_data['data']:
                serializer = SubAccountSerializer(
                    instance=subaccount,
                    data=change,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save(updated_by=validated_data['updated_by'])
            return instance
    return BulkUpdateSubAccountsSerializer

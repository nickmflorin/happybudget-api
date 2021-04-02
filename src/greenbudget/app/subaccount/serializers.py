from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, exceptions

from greenbudget.app.budget_item.serializers import (
    BudgetItemGroupSerializer,
    BudgetItemSimpleSerializer
)
from greenbudget.app.common.serializers import EntitySerializer

from .models import SubAccount, SubAccountGroup


class SubAccountSimpleSerializer(BudgetItemSimpleSerializer):
    name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=False
    )

    class Meta:
        model = SubAccount
        fields = BudgetItemSimpleSerializer.Meta.fields + ('name',)


class SubAccountGroupSerializer(BudgetItemGroupSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=SubAccount.objects.all()
    )

    class Meta:
        model = SubAccountGroup
        nested_fields = BudgetItemGroupSerializer.Meta.fields
        fields = nested_fields + ('children', )
        response = {
            'children': (
                SubAccountSimpleSerializer, {'many': True, 'nested': True})
        }

    def validate_children(self, value):
        # In the case of a POST request, the parent will be in the context. In
        # the case of a PATCH request, the instance will be non-null.
        parent = self.context.get('parent')
        if parent is None:
            parent = self.instance.parent
        for subaccount in value:
            if subaccount.parent != parent:
                raise exceptions.ValidationError(
                    "The subaccount %s does not belong to the same parent "
                    "that the group does (%s)." % (subaccount.pk, parent.pk)
                )
        return value


class SubAccountSerializer(SubAccountSimpleSerializer):
    type = serializers.CharField(read_only=True)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=False
    )
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
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    unit = serializers.ChoiceField(
        required=False,
        choices=SubAccount.UNITS,
        allow_null=True
    )
    unit_name = serializers.CharField(read_only=True)
    budget = serializers.PrimaryKeyRelatedField(read_only=True)
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)
    account = serializers.IntegerField(read_only=True, source='account.pk')
    object_id = serializers.IntegerField(read_only=True)
    parent_type = serializers.ChoiceField(
        choices=["account", "subaccount"],
        read_only=True
    )
    subaccounts = SubAccountSimpleSerializer(many=True, read_only=True)
    group = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=SubAccountGroup.objects.all(),
        allow_null=True
    )

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + (
            'identifier', 'name', 'description', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'quantity', 'rate', 'multiplier',
            'unit', 'unit_name', 'account', 'object_id', 'parent_type',
            'ancestors', 'estimated', 'subaccounts', 'actual', 'variance',
            'budget', 'type', 'group', 'siblings')

    def validate_identifier(self, value):
        # In the case that the serializer is nested and being used in a write
        # context, we do not have access to the context.  Validation will
        # have to be done by the serializer using this serializer in its nested
        # form.
        if self._nested is not True:
            parent = self.context.get('parent')
            if parent is None:
                parent = self.instance.parent
            validator = serializers.UniqueTogetherValidator(
                queryset=parent.budget.items.all(),
                fields=('identifier', ),
            )
            validator({'identifier': value}, self)
        return value

    def validate(self, attrs):
        if self.instance is not None and self.instance.subaccounts.count() != 0:
            if any([field in attrs for field in self.instance.DERIVING_FIELDS]):
                raise exceptions.ValidationError(
                    "Field can only be updated when the sub account is not "
                    "derived."
                )
        return super().validate(attrs)


class SubAccountBulkChangeSerializer(SubAccountSerializer):
    id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=SubAccount.objects.all()
    )

    def validate_id(self, instance):
        account = self.parent.parent.instance
        if account != instance.parent:
            raise exceptions.ValidationError(
                "The sub-account %s does not belong to account %s."
                % (instance.pk, account.pk)
            )
        return instance


class AbstractBulkCreateSubAccountsSerializer(serializers.ModelSerializer):
    data = SubAccountSerializer(many=True, nested=True)

    class Meta:
        abstract = True
        fields = ('data', )

    def update(self, instance, validated_data):
        subaccounts = []
        for payload in validated_data['data']:
            serializer = SubAccountSerializer(data=payload, context={
                'parent': instance
            })
            serializer.is_valid(raise_exception=True)
            # Note that the updated_by argument is the user updating the
            # Account by adding new SubAccount(s), so the SubAccount(s) should
            # be denoted as having been created by this user.
            subaccount = serializer.save(
                updated_by=validated_data['updated_by'],
                created_by=validated_data['updated_by'],
                object_id=instance.pk,
                content_type=ContentType.objects.get_for_model(SubAccount),
                parent=instance,
                budget=instance.budget
            )
            subaccounts.append(subaccount)
        return subaccounts


class AbstractBulkUpdateSubAccountsSerializer(serializers.ModelSerializer):
    data = SubAccountBulkChangeSerializer(many=True, nested=True)

    class Meta:
        abstract = True
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
            subaccount = change['instance']
            del change['instance']
            serializer = SubAccountSerializer(
                instance=subaccount,
                data=change,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=validated_data['updated_by'])
        return instance


class SubAccountBulkCreateSubAccountsSerializer(
        AbstractBulkCreateSubAccountsSerializer):

    class Meta:
        model = SubAccount
        fields = AbstractBulkCreateSubAccountsSerializer.Meta.fields


class SubAccountBulkUpdateSubAccountsSerializer(
        AbstractBulkUpdateSubAccountsSerializer):

    class Meta:
        model = SubAccount
        fields = AbstractBulkUpdateSubAccountsSerializer.Meta.fields

from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.budget.serializers import EntitySerializer
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import (
    BudgetSubAccountGroup,
    TemplateSubAccountGroup
)
from greenbudget.app.tagging.serializers import (
    TagField, TagSerializer, ColorSerializer)

from .models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount, SubAccountUnit)


class SubAccountUnitSerializer(TagSerializer):
    color = ColorSerializer(read_only=True)

    class Meta:
        model = SubAccountUnit
        fields = TagSerializer.Meta.fields + ("color", )


class SubAccountSimpleSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    identifier = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )

    class Meta:
        model = SubAccount
        fields = ('id', 'name', 'identifier', 'type', 'description')


class SubAccountTreeNodeSerializer(SubAccountSimpleSerializer):
    children = serializers.PrimaryKeyRelatedField(
        queryset=BudgetSubAccount.objects.all(),
        source='subaccounts'
    )

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + ('children', )

    def __init__(self, *args, **kwargs):
        # The subset is the set of SubAccount(s) that have been filtered by
        # the search.  Only these SubAccount(s) will be included as children
        # to each node of the tree.
        self._subset = kwargs.pop('subset')
        self._search_path = kwargs.pop('search_path')
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(
            in_search_path=instance in self._search_path,
            children=[
                self.__class__(
                    instance=child,
                    search_path=self._search_path,
                    subset=self._subset
                ).data
                for child in self._subset if child.parent == instance
            ]
        )
        return data


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
    unit = TagField(
        serializer_class=SubAccountUnitSerializer,
        queryset=SubAccountUnit.objects.all(),
        required=False,
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

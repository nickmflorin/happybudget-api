from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.account.models import AccountGroup
from greenbudget.app.user.serializers import UserSerializer

from .models import BudgetItem, BudgetItemGroup


class BudgetItemSimpleSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )

    class Meta:
        model = BudgetItem
        fields = ('id', 'identifier')


class BudgetItemGroupSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    created_by = UserSerializer(nested=True, read_only=True)
    updated_by = UserSerializer(nested=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    color = serializers.ChoiceField(
        required=True,
        choices=[
            "#797695",
            "#ff7165",
            "#80cbc4",
            "#ce93d8",
            "#fed835",
            "#c87987",
            "#69f0ae",
            "#a1887f",
            "#81d4fa",
            "#f75776",
            "#66bb6a",
            "#58add6"
        ]
    )

    class Meta:
        model = BudgetItemGroup
        fields = (
            'id', 'name', 'created_by', 'created_at', 'updated_by',
            'updated_at', 'color', 'estimated', 'actual', 'variance')

    def validate_name(self, value):
        # In the case of a POST request, the parent will be in the context. In
        # the case of a PATCH request, the instance will be non-null.
        parent = self.context.get('parent')
        if parent is None:
            if isinstance(self.instance, AccountGroup):
                parent = self.instance.budget
            else:
                parent = self.instance.parent
        validator = serializers.UniqueTogetherValidator(
            queryset=parent.groups.all(),
            fields=('name', ),
        )
        validator({'name': value}, self)
        return value


class BudgetItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)

    class Meta:
        model = BudgetItem
        fields = ('id', 'identifier', 'type', 'description')


class BudgetItemTreeNodeSerializer(BudgetItemSerializer):
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BudgetItem
        fields = BudgetItemSerializer.Meta.fields + ('children', )

    def get_children(self, instance):
        if instance.subaccounts.count():
            return self.__class__(instance.subaccounts.all(), many=True).data
        return []

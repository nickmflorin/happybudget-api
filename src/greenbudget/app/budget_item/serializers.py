from rest_framework import serializers

from .models import BudgetItem


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

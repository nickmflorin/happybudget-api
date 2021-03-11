from rest_framework import serializers

from .models import BudgetItem


class BudgetItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)

    class Meta:
        model = BudgetItem
        fields = ('id', 'identifier', 'type')

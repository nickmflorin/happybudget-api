from rest_framework import serializers

from greenbudget.app.account.serializers import AccountPdfSerializer
from greenbudget.app.group.serializers import BudgetAccountGroupSerializer

from .models import Budget


class BudgetPdfSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    accounts = AccountPdfSerializer(many=True, read_only=True)
    groups = BudgetAccountGroupSerializer(many=True, read_only=True)

    class Meta:
        model = Budget
        fields = (
            'name', 'actual', 'variance', 'estimated', 'accounts', 'groups')
        read_only_fields = fields

from rest_framework import serializers

from greenbudget.app.account.serializers import AccountPdfSerializer
from greenbudget.app.group.serializers import GroupSerializer

from .models import Budget


class BudgetPdfSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    children = AccountPdfSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = Budget
        fields = (
            'name', 'actual', 'estimated', 'children', 'groups',
            'fringe_contribution', 'markup_contribution')
        read_only_fields = fields

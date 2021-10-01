from rest_framework import serializers

from greenbudget.app.account.serializers import AccountPdfSerializer
from greenbudget.app.group.serializers import GroupSerializer

from .models import Budget


class BudgetPdfSerializer(serializers.ModelSerializer):
    type = serializers.CharField(read_only=True, source='pdf_type')
    name = serializers.CharField(read_only=True)
    children = AccountPdfSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    accumulated_value = serializers.FloatField(read_only=True)
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)

    class Meta:
        model = Budget
        fields = ('name', 'children', 'groups', 'nominal_value', 'type') \
            + Budget.CALCULATED_FIELDS
        read_only_fields = fields

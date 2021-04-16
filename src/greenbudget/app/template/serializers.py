from greenbudget.app.budget.serializers import BaseBudgetSerializer
from .models import Template


class TemplateSerializer(BaseBudgetSerializer):
    class Meta:
        model = Template
        fields = BaseBudgetSerializer.Meta.fields

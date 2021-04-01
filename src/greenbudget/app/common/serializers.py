from rest_framework import serializers

from greenbudget.app.budget.models import Budget
from greenbudget.app.account.models import Account
from greenbudget.app.subaccount.models import SubAccount


class AncestorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)
    description = serializers.SerializerMethodField(read_only=True)

    def get_type(self, instance):
        if isinstance(instance, Budget):
            return "budget"
        elif isinstance(instance, Account):
            return "account"
        else:
            assert isinstance(instance, SubAccount)
            return "subaccount"

    def get_description(self, instance):
        if isinstance(instance, Budget):
            return instance.name
        return instance.description

    def get_identifier(self, instance):
        if isinstance(instance, Budget):
            return instance.name
        return instance.identifier

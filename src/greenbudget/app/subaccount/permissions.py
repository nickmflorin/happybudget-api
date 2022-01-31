from greenbudget.app.budget.permissions import (
    BudgetProductPermission, BudgetOwnershipPermission)


class SubAccountOwnershipPermission(BudgetOwnershipPermission):
    object_name = 'subaccount'

    def get_permissioned_obj(self, obj):
        return obj.budget


class SubAccountProductPermission(BudgetProductPermission):
    object_name = 'subaccount'

    def get_permissioned_obj(self, obj):
        return obj.budget

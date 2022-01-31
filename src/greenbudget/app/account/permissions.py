from greenbudget.app.budget.permissions import (
    BudgetProductPermission, BudgetOwnershipPermission)


class AccountOwnershipPermission(BudgetOwnershipPermission):
    object_name = 'account'

    def get_permissioned_obj(self, obj):
        return obj.parent


class AccountProductPermission(BudgetProductPermission):
    object_name = 'account'

    def get_permissioned_obj(self, obj):
        return obj.parent

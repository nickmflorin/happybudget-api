from greenbudget.app.authentication.permissions import (
    AdminPermissionMixin, IsOwner)
from greenbudget.app.budget.permissions import BudgetProductPermission

from .models import TemplateSubAccount


class SubAccountOwnershipPermission(AdminPermissionMixin, IsOwner):
    message = "The user must does not have permission to view this sub account."
    code = "subaccount_permission_error"

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, TemplateSubAccount):
            if obj.budget.community is True:
                return self.has_admin_permission(request, view)
            return super().has_object_permission(request, view, obj)
        return super().has_object_permission(request, view, obj)


class SubAccountProductPermission(BudgetProductPermission):
    access_entity_name = 'subaccount'

    def get_budget(self, obj):
        return obj.budget

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, TemplateSubAccount):
            return super().has_object_permission(request, view, obj)
        return True

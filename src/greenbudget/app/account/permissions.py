from greenbudget.app.authentication.exceptions import PermissionErrorCodes
from greenbudget.app.authentication.permissions import (
    AdminPermissionMixin, IsOwner)
from greenbudget.app.budget.permissions import BudgetProductPermission

from .models import TemplateAccount


class AccountOwnershipPermission(AdminPermissionMixin, IsOwner):
    message = "The user must does not have permission to view this account."
    code = PermissionErrorCodes.PERMISSION_ERROR

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, TemplateAccount):
            if obj.parent.community is True:
                return self.has_admin_permission(request, view)
            return super().has_object_permission(request, view, obj)
        return super().has_object_permission(request, view, obj)


class AccountProductPermission(BudgetProductPermission):
    access_entity_name = 'account'

    def get_budget(self, obj):
        return obj.budget

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, TemplateAccount):
            return super().has_object_permission(request, view, obj)
        return True

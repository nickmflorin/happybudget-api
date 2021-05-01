from greenbudget.app.common.permissions import AdminPermissionMixin, IsOwner

from .models import TemplateAccount


class AccountObjPermission(AdminPermissionMixin, IsOwner):
    message = "The user must does not have permission to view this account."
    # This doesn't seem to work with the .permission_denied() method in the
    # current version of DRF - but it does in the latest version.
    code = "account_permission_error"

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, TemplateAccount):
            if obj.budget.community is True:
                return self.has_admin_permission(request, view)
            return super().has_object_permission(request, view, obj)
        return super().has_object_permission(request, view, obj)

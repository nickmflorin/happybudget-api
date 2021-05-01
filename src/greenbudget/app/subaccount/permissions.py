from greenbudget.app.common.permissions import AdminPermissionMixin, IsOwner

from .models import TemplateSubAccount


class SubAccountObjPermission(AdminPermissionMixin, IsOwner):
    message = "The user must does not have permission to view this sub account."
    # This doesn't seem to work with the .permission_denied() method in the
    # current version of DRF - but it does in the latest version.
    code = "subaccount_permission_error"

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, TemplateSubAccount):
            if obj.budget.community is True:
                return self.has_admin_permission(request, view)
            return super().has_object_permission(request, view, obj)
        return super().has_object_permission(request, view, obj)

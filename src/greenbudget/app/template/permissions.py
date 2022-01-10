from greenbudget.app.authentication.exceptions import PermissionErrorCodes
from greenbudget.app.authentication.permissions import (
    AdminPermissionMixin, IsOwner)


class TemplateObjPermission(AdminPermissionMixin, IsOwner):
    message = "The user must does not have permission to view this template."
    code = PermissionErrorCodes.PERMISSION_ERROR

    def has_object_permission(self, request, view, obj):
        if obj.community is True:
            return self.has_admin_permission(request, view)
        return super().has_object_permission(request, view, obj)

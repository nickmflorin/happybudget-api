from greenbudget.app.authentication.permissions import (
    AdminPermissionMixin, IsOwner)


class ActualObjPermission(AdminPermissionMixin, IsOwner):
    message = "The user must does not have permission to view this actual."
    # This doesn't seem to work with the .permission_denied() method in the
    # current version of DRF - but it does in the latest version.
    code = "actual_permission_error"

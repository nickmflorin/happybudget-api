from greenbudget.app.authentication.permissions import (
    AdminPermissionMixin, IsOwner)

from .models import Contact


class ContactObjPermission(AdminPermissionMixin, IsOwner):
    message = "The user must does not have permission to view this contact."
    # This doesn't seem to work with the .permission_denied() method in the
    # current version of DRF - but it does in the latest version.
    code = "contact_permission_error"

    def get_contact_queryset(self, request, *args, **kwargs):
        return Contact.objects.all()

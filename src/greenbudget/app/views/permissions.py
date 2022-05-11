from django.conf import settings

from happybudget.app import permissions


def to_view_permission(pms):
    view_permission = permissions.AND(permissions.instantiate_permissions(pms))
    # If staff users are granted global permissions, grant permission
    # access for authenticated staff users.
    if settings.STAFF_USER_GLOBAL_PERMISSIONS is True:
        view_permission = permissions.OR(view_permission, permissions.AND(
            permissions.IsFullyAuthenticated(affects_after=True),
            permissions.IsStaffUser
        ))
    return view_permission

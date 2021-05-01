from rest_framework import permissions


class BudgetObjPermission(permissions.BasePermission):
    message = "The user must does not have permission to view this budget."
    # This doesn't seem to work with the .permission_denied() method in the
    # current version of DRF - but it does in the latest version.
    code = "budget_permission_error"

    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user

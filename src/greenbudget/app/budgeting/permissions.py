from greenbudget.app import permissions


class IsBudgetDomain(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.domain == 'budget'

from rest_framework import permissions


class AdminPermissionMixin:
    def has_admin_permission(self, request, view):
        admin_permission = permissions.IsAdminUser()
        return admin_permission.has_permission(request, view)


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        owner_field = getattr(view, 'owner_field', 'created_by')
        return getattr(obj, owner_field) == request.user


class IsOwnerOrReadOnly(IsOwner):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_object_permission(request, view, obj)


def PermissionOnWrite(permission_cls):
    class _PermissionOnWrite(permission_cls):
        def has_permission(self, request, view):
            if request.method in permissions.SAFE_METHODS:
                return True
            return super().has_permission(request, view)

        def has_object_permission(self, request, view, obj):
            if request.method in permissions.SAFE_METHODS:
                return True
            return super().has_object_permission(request, view, obj)
    return _PermissionOnWrite


IsAdminOrReadOnly = PermissionOnWrite(permissions.IsAdminUser)

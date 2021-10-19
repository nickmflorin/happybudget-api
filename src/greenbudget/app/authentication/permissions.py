from rest_framework import permissions

from .exceptions import (
    NotAuthenticatedError, AccountDisabledError, EmailNotVerified,
    EmailVerified)


class UserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        force_logout = getattr(view, 'force_logout', None)
        return self.user_has_permission(user, force_logout=force_logout)


class IsAuthenticated(UserPermission):
    def user_has_permission(self, user, force_logout=False):
        if user is None or not user.is_authenticated:
            raise NotAuthenticatedError(
                force_logout=force_logout and user.is_authenticated
            )
        if not user.is_active:
            raise AccountDisabledError(
                user_id=getattr(user, 'pk'),
                force_logout=force_logout
            )
        return True


class IsNotVerified(UserPermission):
    def user_has_permission(self, user, force_logout=False):
        if user is None or not user.is_authenticated:
            raise Exception(
                "The `IsNotVerified` permission should always come after the "
                "`IsAuthenticated` permission."
            )
        if user.is_verified:
            raise EmailVerified(user_id=getattr(user, 'pk'))
        return True


class IsVerified(UserPermission):
    def user_has_permission(self, user, force_logout=False):
        if user is None or not user.is_authenticated:
            raise Exception(
                "The `IsVerified` permission should always come after the "
                "`IsAuthenticated` permission."
            )
        if not user.is_verified:
            raise EmailNotVerified(
                user_id=getattr(user, 'pk'),
                force_logout=force_logout
            )
        return True


class IsAnonymous(permissions.BasePermission):
    message = "User already has an active session."

    def has_permission(self, request, view):
        return request.user is None or not request.user.is_authenticated


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

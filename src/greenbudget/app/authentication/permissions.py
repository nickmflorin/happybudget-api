from rest_framework import permissions

from django.conf import settings

from greenbudget.lib.utils import import_at_module_path
from .exceptions import (
    NotAuthenticatedError, AccountDisabledError, EmailNotVerified,
    EmailVerified, PermissionDenied)


class UserPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        return self.user_has_permission(user)


class IsAuthenticated(UserPermission):
    def user_has_permission(self, user, force_logout=True):
        if user is None or not user.is_authenticated:
            raise NotAuthenticatedError(force_logout=force_logout)
        if not user.is_active:
            raise AccountDisabledError(
                user_id=getattr(user, 'pk'),
                force_logout=force_logout
            )
        return True


class IsVerified(UserPermission):
    def user_has_permission(self, user, force_logout=True):
        assert not (user is None or not user.is_authenticated), \
            "This permission should always be preceeded by `IsAuthenticated`."
        if not user.is_verified:
            raise EmailNotVerified(
                user_id=getattr(user, 'pk'),
                force_logout=force_logout
            )
        return True


def get_default_permissions():
    permission_paths = settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']
    return [import_at_module_path(p) for p in permission_paths]


def check_user_permissions(user, permissions=None, force_logout=True):
    """
    A method to evaluate a set of permisisons that extend :obj:`UserPermission`
    in cases where we want to raise instances of
    :obj:`exceptions.PermissionDenied` outside of the scope of DRF's
    permissioning on views.
    """
    permissions = permissions or get_default_permissions()
    permissions = [p() if isinstance(p, type) else p for p in permissions]
    for permission in permissions:
        assert hasattr(permission, 'user_has_permission'), \
            "Permission must extend `UserPermission`."

        if not permission.user_has_permission(user, force_logout=force_logout):
            # The individual UserPermission(s) instances should raise a
            # PermissionDenied exception, but we do here just in case for
            # completeness sake.
            raise PermissionDenied(
                detail=getattr(permission, 'message', None),
                force_logout=force_logout
            )


class IsNotVerified(UserPermission):
    def user_has_permission(self, user, force_logout=False):
        # Force logout param is required for checking permissions manually via
        # the views.
        assert not (user is None or not user.is_authenticated), \
            "This permission should always be preceeded by `IsAuthenticated`."
        if user.is_verified:
            raise EmailVerified(user_id=getattr(user, 'pk'))
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

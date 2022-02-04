from rest_framework import permissions

from django.conf import settings

from greenbudget.lib.utils import import_at_module_path

from .exceptions import (
    NotAuthenticatedError,
    AccountDisabled,
    AccountNotVerified,
    PermissionErrorCodes
)


class BasePermission(permissions.BasePermission):
    message = "The user does not have the correct permission to perform this action."  # noqa
    code = PermissionErrorCodes.PERMISSION_ERROR


class UserPermission(BasePermission):

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        return self.user_has_permission(user)


class IsAuthenticated(UserPermission):
    """
    Permission that ensures that the active user's account is both authenticated
    and active.
    """

    def user_has_permission(self, user):
        if user is None or not user.is_authenticated:
            raise NotAuthenticatedError()
        return True


class IsActive(UserPermission):
    """
    Permission that ensures that the active user's account is active.
    """

    def user_has_permission(self, user):
        assert not (user is None or not user.is_authenticated), \
            "This permission should always be preceeded by `IsAuthenticated`."
        if not user.is_active:
            raise AccountDisabled(user_id=getattr(user, 'pk'))
        return True


class IsVerified(UserPermission):
    """
    Permission that ensures that the active user's account is verified.
    """

    def user_has_permission(self, user):
        assert not (user is None or not user.is_authenticated), \
            "This permission should always be preceeded by `IsAuthenticated`."
        if not user.email_is_verified:
            raise AccountNotVerified(user_id=getattr(user, 'pk'))
        return True


def instantiate_permissions(permissions):
    return [p() if isinstance(p, type) else p for p in permissions]


def get_default_permissions():
    permission_paths = settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']
    return [import_at_module_path(p) for p in permission_paths]


def check_user_permissions(user, permissions=None):
    """
    A method to evaluate a set of permisisons that extend :obj:`UserPermission`
    in cases where we want to raise instances of
    :obj:`exceptions.NotAuthenticatedError` outside of the scope of DRF's
    permissioning on views.
    """
    permissions = permissions if permissions is not None \
        else get_default_permissions()
    for permission in instantiate_permissions(permissions):
        assert hasattr(permission, 'user_has_permission'), \
            "Permission must extend `UserPermission`."

        if not permission.user_has_permission(user):
            # The individual UserPermission(s) instances should raise a
            # NotAuthenticatedError exception, but we do here just in case for
            # completeness sake.
            raise NotAuthenticatedError(
                detail=getattr(permission, 'message', None)
            )


class IsAnonymous(BasePermission):
    """
    Permission that ensures that a user is not already logged in.  The
    purpose is to prevent actively logged in users from performing processes
    that are only pertinent to users that are not logged in (i.e. forgot
    password functionality).

    This is meant to be used so a malicious attacker could not hijack an
    actively logged in user's account and attempt to expose security holes in
    processes (such as forgot password functionality) in order to get
    sensitive information about that user.
    """
    message = "User already has an active session."

    def has_permission(self, request, view):
        return request.user is None or not request.user.is_authenticated


class AdminPermissionMixin:
    def has_admin_permission(self, request, view):
        admin_permission = permissions.IsAdminUser()
        return admin_permission.has_permission(request, view)


class IsOwner(BasePermission):
    """
    Object level permission that ensures that the object that an actively logged
    in user is accessing was created by that user.
    """

    def has_object_permission(self, request, view, obj):
        owner_field = getattr(view, 'owner_field', 'created_by')
        return getattr(obj, owner_field) == request.user


class IsOwnerOrReadOnly(IsOwner):
    """
    Object level permission that ensures that the object that an actively logged
    in user is accessing was created by that user for write operations, but
    allows all users to access that object for read operations.
    """

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

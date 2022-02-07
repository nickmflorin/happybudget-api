from rest_framework import permissions

from greenbudget.app.authentication.exceptions import (
    NotAuthenticatedError,
    AccountDisabled,
    AccountNotVerified
)
from greenbudget.app.authentication.utils import request_is_safe_method
from .base import BasePermission
from .operators import AND


def PermissionOnWrite(permission_cls):
    class _PermissionOnWrite(permission_cls):
        def has_permission(self, request, view):
            if request_is_safe_method(request):
                return True
            return super().has_permission(request, view)

        def has_object_permission(self, request, view, obj):
            if request_is_safe_method(request):
                return True
            return super().has_object_permission(request, view, obj)
    return _PermissionOnWrite


class AllowAny(BasePermission):
    def has_permission(self, request, view):
        return True


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


IsAdminOrReadOnly = PermissionOnWrite(IsAdminUser)


class IsAuthenticated(BasePermission):
    """
    Permission that ensures that the active user's account is both authenticated
    and active.
    """
    exception_class = NotAuthenticatedError

    def has_user_permission(self, user):
        if user is None or not user.is_authenticated:
            self.permission_denied()
        return True


class IsActive(BasePermission):
    """
    Permission that ensures that the active user's account is active.
    """
    exception_class = AccountDisabled

    def has_user_permission(self, user):
        assert user.is_authenticated, \
            f"Permission class {self.__class__.__name__} should always be " \
            "preceeded by a permission class that guarantees authentication."
        if not user.is_active:
            self.permission_denied(user_id=getattr(user, 'pk'))
        return True


class IsVerified(BasePermission):
    """
    Permission that ensures that the active user's account is verified.
    """
    exception_class = AccountNotVerified

    def has_user_permission(self, user):
        assert user.is_authenticated, \
            f"Permission class {self.__class__.__name__} should always be " \
            "preceeded by a permission class that guarantees authentication."
        if not user.email_is_verified:
            self.permission_denied(user_id=getattr(user, 'pk'))
        return True


IsFullyAuthenticated = AND(
    IsAuthenticated(affects_after=True),
    IsActive,
    IsVerified
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
    object_name = "object"
    message = "The user must does not have permission to view this {object_name}."  # noqa

    def __init__(self, owner_field='created_by', object_name=None, **kwargs):
        self._owner_field = owner_field
        self._object_name = object_name
        super().__init__(**kwargs)

    def has_object_permission(self, request, view, obj):
        return getattr(obj, self._owner_field) == request.user


class IsOwnerOrReadOnly(IsOwner):
    """
    Object level permission that ensures that the object that an actively logged
    in user is accessing was created by that user for write operations, but
    allows all users to access that object for read operations.
    """

    def has_permission(self, request, view):
        return request_is_safe_method(request)

    def has_object_permission(self, request, view, obj):
        if request_is_safe_method(request):
            return True
        return super().has_object_permission(request, view, obj)


class IsShared(BasePermission):
    exception_class = NotAuthenticatedError

    def has_permission(self, request, view):
        return request.share_token.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.share_token.is_authenticated \
            and request.share_token.instance == obj


class IsRequestMethod(BasePermission):
    def __init__(self, *methods):
        self._methods = list(methods)
        super().__init__(*methods)

    def has_permission(self, request, view):
        return request.method.upper() in [m.upper() for m in self._methods]

    def has_object_permission(self, request, view, obj):
        return request.method.upper() in [m.upper() for m in self._methods]


class IsSafeRequestMethod(BasePermission):
    def has_permission(self, request, view):
        return request_is_safe_method(request)

    def has_object_permission(self, request, view, obj):
        return request_is_safe_method(request)


class IsWriteRequestMethod(BasePermission):
    def has_permission(self, request, view):
        return not request_is_safe_method(request)

    def has_object_permission(self, request, view, obj):
        return not request_is_safe_method(request)


class IsViewAction(BasePermission):
    def __init__(self, *actions):
        self._actions = list(actions)
        super().__init__(*actions)

    def has_permission(self, request, view):
        return view.action in self._actions

    def has_object_permission(self, request, view, obj):
        return view.action in self._actions


class IsNotViewAction(BasePermission):
    def __init__(self, *actions):
        self._actions = list(actions)
        super().__init__(*actions)

    def has_permission(self, request, view):
        return view.action not in self._actions

    def has_object_permission(self, request, view, obj):
        return view.action not in self._actions

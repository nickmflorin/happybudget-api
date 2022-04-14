from greenbudget.app.authentication.exceptions import (
    NotAuthenticatedError,
    AccountDisabled,
    AccountNotVerified
)
from .base import BasePermission
from .operators import AND
from .request import request_is_safe_method


class IsAuthenticated(BasePermission):
    """
    Permission that ensures that the active user's account is both authenticated
    and active.
    """
    exception_class = NotAuthenticatedError
    affects_after = True

    def has_user_permission(self, user):
        if user is None or not user.is_authenticated:
            self.permission_denied()
        return True


class IsActive(BasePermission):
    """
    Permission that ensures that the active user's account is active.
    """
    exception_class = AccountDisabled
    user_dependency_flags = ['is_authenticated']

    def has_user_permission(self, user):
        if not user.is_active:
            self.permission_denied(user_id=getattr(user, 'pk'))
        return True


class IsVerified(BasePermission):
    """
    Permission that ensures that the active user's account is verified.
    """
    exception_class = AccountNotVerified
    user_dependency_flags = ['is_authenticated']

    def has_user_permission(self, user):
        if not user.email_is_verified:
            self.permission_denied(user_id=getattr(user, 'pk'))
        return True


IsFullyAuthenticated = AND(IsAuthenticated, IsActive, IsVerified)


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
    pass


class IsStaffUser(BasePermission):
    user_dependency_flags = ['is_authenticated', 'is_active', 'is_verified']

    def has_permission(self, request, view):
        print("IS STAFF: %s" % request.user.is_staff)
        return bool(request.user and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_staff)


IsStaffUserOrReadOnly = PermissionOnWrite(IsStaffUser)


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


class StaffUserPermissionMixin:
    def has_staff_permission(self, request, view):
        staff_permission = IsStaffUser()
        return staff_permission.has_permission(request, view)


class IsOwner(BasePermission):
    """
    Object level permission that ensures that the object that an actively logged
    in user is accessing was created by that user.
    """
    object_name = "object"
    user_dependency_flags = ['is_authenticated', 'is_active', 'is_verified']
    message = (
        "The user must does not have permission to view this "
        "{object_name}."
    )

    def __init__(self, owner_field='created_by', object_name=None, **kwargs):
        self._owner_field = owner_field
        self._object_name = object_name
        super().__init__(**kwargs)

    def has_object_permission(self, request, view, obj):
        return getattr(obj, self._owner_field) == request.user


class IsPublic(BasePermission):
    exception_class = NotAuthenticatedError

    def has_permission(self, request, view):
        return request.public_token.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.public_token.is_authenticated \
            and request.public_token.instance == obj


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

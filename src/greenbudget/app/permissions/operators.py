import functools

from greenbudget.app.authentication.exceptions import NotAuthenticatedError

from .base import BasePermission
from .exceptions import PermissionError
from .utils import instantiate_permissions


class Operator(BasePermission):

    def __init__(self, *permissions, **kwargs):
        permissions = list(permissions)
        if len(permissions) == 1 and isinstance(permissions[0], (tuple, list)):
            permissions = list(permissions[0])
        super().__init__(*permissions, **kwargs)
        self._permissions = permissions
        self._failed_permissions = []

    @property
    def failed_permissions(self):
        return self._failed_permissions

    @property
    def permissions(self):
        return instantiate_permissions(self._permissions)

    def has_permission(self, request, view):
        return self.evaluate('has_permission', request, view)

    def has_object_permission(self, request, view, obj):
        return self.evaluate('has_object_permission', request, view, obj)

    @property
    def failed_priority_permission(self):
        if self.failed_permissions:
            priorities = [
                p for p in self.failed_permissions
                if p[0].priority
            ]
            prior = priorities[0] if priorities else self.failed_permissions[0]
            if isinstance(prior[0], Operator):
                assert prior[0].failed_priority_permission is not None
                return prior[0].failed_priority_permission
            return prior
        return None

    def handle_failed_permissions(self):
        if self.failed_priority_permission:
            raise self.failed_priority_permission[1]
        return True

    def permission_denied(self, **kwargs):
        assert self.failed_priority_permission is not None, \
            "Can only call permission denied on operators after they have " \
            "been evaluated."
        self.failed_priority_permission[0].permission_denied(**kwargs)


def track_failed_permissions(**kw):
    def decorator(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            instance._failed_permissions = []
            for permission in instance.permissions:
                evaluated = func(instance, permission, *args, **kwargs)
                # If the returned value is None, that means the permission is
                # not applicable.
                if evaluated is None:
                    continue
                # If the value is True, that means that the permission was
                # granted.  In the case of an OR clause, we can exit the
                # permission check of the operator early since one permission
                # was granted.
                if evaluated is True:
                    if kw.get('exit_on_grant', False):
                        return evaluated
                    continue
                else:
                    # The permission returning the value of False, a string
                    # error message or a PermissionError indicates that the
                    # permission was not granted.
                    assert evaluated is False or isinstance(evaluated, str) \
                        or isinstance(evaluated,
                            (PermissionError, NotAuthenticatedError)), \
                        f"Unexpected type {type(evaluated)} returned from " \
                        f"permission method.  Expected either a string, a " \
                        "boolean or a PermissionError."

                    instance._failed_permissions.append((permission, evaluated))
                    # If the permission is required to be granted for subsequent
                    # permissions, and the permission failed - we need to exit
                    # early.
                    if permission.affects_after \
                            and kw.get('break_after_failure', False):
                        break
            return instance.handle_failed_permissions()
        return inner
    return decorator


class AND(Operator):
    """
    A better version of :obj:`rest_framework.permissions.AND` that takes into
    account permissions later in the sequence that assume they are only being
    evaluated if permissions earlier in the sequence granted access.

    Grants permission only if all of the applicable children permission classes
    grant permission.
    """
    @track_failed_permissions(break_after_failure=True)
    def has_user_permission(self, permission, user):
        try:
            return permission.has_user_permission(user, raise_exception=True)
        except (PermissionError, NotAuthenticatedError) as e:
            return e

    @track_failed_permissions(break_after_failure=True)
    def evaluate(self, permission, method, *args):
        try:
            return getattr(permission, method)(*args, raise_exception=True)
        except (PermissionError, NotAuthenticatedError) as e:
            return e


class OR(Operator):
    """
    A better version of :obj:`rest_framework.permissions.OR` that takes into
    account the applicability and other characteristics of each child permission
    class as they relate to the overall sequence of permission classes.

    Grants permission only if at least one of the applicable children permission
    classes grant permission.
    """
    @track_failed_permissions(exit_on_grant=True)
    def has_user_permission(self, permission, user):
        # Do not immediately raise the exception, but store it - such
        # that we can determine after all permissions have been checked
        # which failing permission the exception should be raised for.
        return permission.has_user_permission(user, raise_exception=False)

    @track_failed_permissions(exit_on_grant=True)
    def evaluate(self, permission, method, request, view, *args):
        # The permission class will evaluate to True if it is not applicable,
        # but we do not want that True value to contribute to the OR clause
        # evaluating to True - since the permission is not applicable.
        if permission.is_applicable(request, view):
            # Do not immediately raise the exception, but store it - such
            # that we can determine after all permissions have been checked
            # which failing permission the exception should be raised for.
            return getattr(permission, method)(
                request, view, *args, raise_exception=False)
        return None

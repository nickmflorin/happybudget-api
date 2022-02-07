import functools

from .base import BasePermission
from .constants import (
    ObjectContext, PErrors, PermissionOperation, PermissionContext, ViewContext)
from .utils import instantiate_permissions


class Operator(BasePermission):

    def __init__(self, *permissions, **kwargs):
        permissions = list(permissions)
        if len(permissions) == 1 and isinstance(permissions[0], (tuple, list)):
            permissions = list(permissions[0])
        super().__init__(*permissions, **kwargs)
        self._permissions = permissions
        self._failed_permissions = []
        self._default = kwargs.pop('default', None)

    @property
    def failed_permissions(self):
        return self._failed_permissions

    @property
    def permissions(self):
        return instantiate_permissions(self._permissions)

    def permissions_for_context(self, context, *args):
        pms = self.permissions[:]
        if context == PermissionContext.VIEW:
            pms = [
                p for p in pms
                if p.is_view_applicable(self.view_context(*args))
            ]
        elif context == PermissionContext.OBJECT:
            pms = [
                p for p in pms
                if p.is_object_applicable(self.object_context(*args))
            ]
        if len(pms) == 0 and self._default is not None:
            if isinstance(self._default, BaseException):
                raise self._default
            return [self._default]
        return pms

    def view_context(self, request, view):
        return ViewContext(request=request, view=view)

    def object_context(self, request, view, obj):
        return ObjectContext(request=request, view=view, obj=obj)

    @property
    def failed_priority_permission(self):
        if self.failed_permissions:
            priorities = [
                p for p in self.failed_permissions
                if p[1] is True
            ]
            prior = priorities[0] if priorities else self.failed_permissions[0]
            if isinstance(prior[0], Operator):
                assert prior[0].failed_priority_permission is not None
                return prior[0].failed_priority_permission
            return prior
        return None

    def handle_failed_permissions(self):
        if self.failed_priority_permission:
            priority = self.failed_priority_permission
            assert priority[2] is not True
            if isinstance(priority[2], PErrors):
                raise priority[2]
            elif isinstance(priority[2], str):
                priority[0].permission_denied(message=priority[1])
            else:
                priority[0].permission_denied()
        return True

    def permission_denied(self, **kwargs):
        assert self.failed_priority_permission is not None, \
            "Can only call permission denied on operators after they have " \
            "been evaluated."
        self.failed_priority_permission[0].permission_denied(**kwargs)


def track_failed_permissions(context):
    def decorator(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            instance._failed_permissions = []
            permissions = instance.permissions_for_context(context, *args)
            for permission in permissions:
                try:
                    evaluated = func(instance, permission, *args, **kwargs)
                except PErrors as e:
                    evaluated = e
                # If the value is True, that means that the permission was
                # granted.  In the case of an OR clause, we can exit the
                # permission check of the operator early since one permission
                # was granted.
                if evaluated is True:
                    if instance.operation == PermissionOperation.OR:
                        return evaluated
                    continue
                else:
                    # The permission returning the value of False, a string
                    # error message or a PermissionError indicates that the
                    # permission was not granted.
                    assert evaluated is False or isinstance(evaluated, str) \
                        or isinstance(evaluated, PErrors), \
                        f"Unexpected type {type(evaluated)} returned from " \
                        f"permission method.  Expected either a string, a " \
                        "boolean or a PermissionError."

                    prioritized = permission.is_prioritized(*args[:1])

                    instance._failed_permissions.append(
                        (permission, prioritized, evaluated))
                    # If the permission is required to be granted for subsequent
                    # permissions, and the permission failed - we need to exit
                    # early.
                    if permission.affects_after \
                            and instance.operation == PermissionOperation.AND:
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
    operation = PermissionOperation.AND

    @track_failed_permissions(context=PermissionContext.OBJECT)
    def has_object_permission(self, permission, *args):
        return permission.has_object_permission(*args, raise_exception=True)

    @track_failed_permissions(context=PermissionContext.VIEW)
    def has_permission(self, permission, *args):
        return permission.has_permission(*args, raise_exception=True)


class OR(Operator):
    """
    A better version of :obj:`rest_framework.permissions.OR` that takes into
    account the applicability and other characteristics of each child permission
    class as they relate to the overall sequence of permission classes.

    Grants permission only if at least one of the applicable children permission
    classes grant permission.
    """
    operation = PermissionOperation.OR

    @track_failed_permissions(context=PermissionContext.OBJECT)
    def has_object_permission(self, permission, *args):
        return permission.has_object_permission(*args, raise_exception=False)

    @track_failed_permissions(context=PermissionContext.VIEW)
    def has_permission(self, permission, *args):
        return permission.has_permission(*args, raise_exception=False)

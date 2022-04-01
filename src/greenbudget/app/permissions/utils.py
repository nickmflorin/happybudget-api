from django.conf import settings

from greenbudget.lib.utils import import_at_module_path
from greenbudget.app.authentication.exceptions import NotAuthenticatedError

from .constants import PErrors
from .exceptions import PermissionErr


def instantiate_permissions(ps):
    ps = [import_at_module_path(p) if isinstance(p, str) else p for p in ps]
    return [p() if isinstance(p, type) else p for p in ps]


def get_default_permissions():
    return instantiate_permissions(
        settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'])


def get_auth_permissions():
    return instantiate_permissions(settings.AUTHENTICATION_PERMISSION_CLASSES)


def check_user_permissions(user, **kwargs):
    """
    A method to evaluate a set of permissions that extend :obj:`UserPermission`
    for a given :obj:`User`.
    """
    default_permissions = kwargs.pop(
        'default_permissions',
        settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']
    )
    permissions = kwargs.pop('permissions', default_permissions)
    default_exception_class = kwargs.pop(
        'default_exception_class', PermissionErr)
    raise_exception = kwargs.pop('raise_exception', True)

    for permission in instantiate_permissions(permissions):
        assert hasattr(permission, 'has_user_perm'), \
            f"The permission class {permission.__class__} does not have a " \
            "user permission method."
        try:
            has_permission = permission.has_user_perm(
                user, raise_exception=True)
        except PErrors as e:
            if raise_exception:
                raise e
            return False
        if not has_permission:
            if raise_exception:
                raise default_exception_class(
                    detail=getattr(permission, 'message', None))
            return False
    return True


def check_user_auth_permissions(user, raise_exception=True):
    return check_user_permissions(
        user=user,
        default_exception_class=NotAuthenticatedError,
        default_permissions=settings.AUTHENTICATION_PERMISSION_CLASSES,
        raise_exception=raise_exception
    )

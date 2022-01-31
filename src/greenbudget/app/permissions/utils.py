from django.conf import settings

from greenbudget.lib.utils import import_at_module_path
from greenbudget.app.authentication.exceptions import NotAuthenticatedError


def instantiate_permissions(permissions):
    return [p() if isinstance(p, type) else p for p in permissions]


def get_default_permissions():
    permission_paths = settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']
    return [import_at_module_path(p) for p in permission_paths]


def check_user_permissions(user, permissions=None, raise_exception=True):
    """
    A method to evaluate a set of permisisons that extend :obj:`UserPermission`
    in cases where we want to raise instances of
    :obj:`exceptions.NotAuthenticatedError` outside of the scope of DRF's
    permissioning on views.
    """
    permissions = permissions if permissions is not None \
        else get_default_permissions()
    for permission in instantiate_permissions(permissions):
        if not permission.has_user_permission(user,
                raise_exception=raise_exception):
            # The individual UserPermission(s) instances should raise a
            # NotAuthenticatedError exception, but we do here just in case for
            # completeness sake.
            raise NotAuthenticatedError(
                detail=getattr(permission, 'message', None)
            )

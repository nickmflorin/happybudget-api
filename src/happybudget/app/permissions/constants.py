from happybudget.app.authentication.exceptions import NotAuthenticatedError
from .exceptions import PermissionErr


PErrors = (PermissionErr, NotAuthenticatedError)


class PermissionContext:
    OBJECT = "object"
    VIEW = "view"

    def __init__(self, request, view):
        self.view = view
        self.request = request

    @classmethod
    def from_args(cls, *args):
        """
        Returns either the :obj:`ObjectContext` or :obj:`ViewContext` depending
        on whether or not the object is included in the permission check
        arguments.

        The arguments will always include the `view` and the `request`, but the
        `obj` argument is only provided when in the context of the
        `check_obj_perm` method.
        """
        if len(args) == 2:
            return ViewContext(*args)
        return ObjectContext(*args)


class PermissionOperation:
    AND = "AND"
    OR = "OR"


class ViewContext(PermissionContext):
    context_type = PermissionContext.VIEW


class ObjectContext(PermissionContext):
    context_type = PermissionContext.OBJECT

    def __init__(self, request, view, obj):
        super().__init__(request, view)
        self.obj = obj

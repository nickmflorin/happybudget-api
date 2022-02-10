import collections

from greenbudget.app.authentication.exceptions import NotAuthenticatedError
from .exceptions import PermissionError


PErrors = (PermissionError, NotAuthenticatedError)


class PermissionContext:
    OBJECT = "object"
    VIEW = "view"


class PermissionOperation:
    AND = "AND"
    OR = "OR"


ViewContext = collections.namedtuple('ViewContext', ['view', 'request'])
ObjectContext = collections.namedtuple(
    'ObjectContext', ['view', 'request', 'obj'])
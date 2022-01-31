import copy
from dataclasses import dataclass
import functools
from typing import Union, List

from rest_framework import permissions

from greenbudget.lib.utils import (
    get_string_formatted_kwargs, empty, ensure_iterable, humanize_list)

from greenbudget.app.authentication.exceptions import NotAuthenticatedError
from greenbudget.app.authentication.utils import (
    request_is_safe_method, request_is_write_method)

from .exceptions import PermissionError


@dataclass
class PermissionConfig:
    attr: str
    type: type = None
    default: Union[bool, None] = empty
    required: bool = False
    conflicts: Union[str, List[str]] = empty


def with_raise_exception(func):
    """
    Allows the permission methods on a permission class to be called with a
    `raise_exception` boolean flag, that will either force a PermissionError
    to be raised specific to that permission class or will forcefully suppress
    the PermissionError for that permission class, returning the string message
    associated with the PermissionError that would have otherwise be raised.
    """
    @functools.wraps(func)
    def decorated(instance, *args, **kwargs):
        raise_exception = kwargs.pop('raise_exception', True)
        try:
            evaluated = func(instance, *args, **kwargs)
        except (PermissionError, NotAuthenticatedError) as e:
            if raise_exception is True:
                raise e
            return False
        else:
            if evaluated is False or isinstance(evaluated, str):
                # If the permission method returns a string message, than it
                # indicates that the permission failed and the returned value
                # is the message the PermissionError should have.
                if raise_exception:
                    if evaluated is False:
                        instance.permission_denied()
                    else:
                        instance.permission_denied(message=evaluated)
                return False
            assert evaluated is True, \
                f"Unexpected type {type(evaluated)} returned from " \
                f"permission method {func.__name__}.  Expected either " \
                "a string or a boolean."
            return True
    return decorated


class BasePermissionMetaclass(permissions.BasePermissionMetaclass):
    def __new__(cls, name, bases, dct):
        @with_raise_exception
        def has_permission(instance, request, view):
            if not instance.is_applicable(request, view):
                return True
            elif not instance.has_user_permission(request.user):
                return False
            if instance._get_nested_obj is not None:
                nested_parent = instance._get_nested_obj(view)
                return has_obj_permission(instance, request, view, nested_parent)
            return _has_permission(instance, request, view)

        @with_raise_exception
        def has_user_permission(instance, user):
            return _user_has_permission(instance, user)

        def get_permissioned_obj(instance, obj):
            # If the callback to get the permissioned object was provided on
            # init, it overrides the class method.
            if instance._get_permissioned_obj is not None:
                return instance._get_permissioned_obj(obj)
            elif _get_permissioned_obj is not None:
                return _get_permissioned_obj(instance, obj)
            return obj

        @with_raise_exception
        def has_obj_permission(instance, request, view, obj):
            if not instance.is_applicable(request, view):
                return True
            elif not instance.has_user_permission(request.user):
                return False
            obj = get_permissioned_obj(instance, obj)
            return _has_object_permission(instance, request, view, obj)

        def permission_message(instance, original_message):
            formatted = original_message
            fkwargs = get_string_formatted_kwargs(formatted)
            for k in fkwargs:
                fvalue = getattr(
                    instance, k, getattr(instance, f"_{k}", None))
                if fvalue is not None:
                    formatted = formatted.replace("{%s}" % k, fvalue)
            return formatted

        if 'message' in dct:
            msg = dct["message"]
            dct['message'] = property(
                lambda instance, k=msg: permission_message(instance, k))

        klass = super().__new__(cls, name, bases, dct)

        # It is important that the permission_denied operations on a permission
        # class raise the appropriate error, such that it can be properly
        # handled in sequences of permissions and/or communicated to the FE.
        if not issubclass(getattr(klass, 'exception_class'),
                (PermissionError, NotAuthenticatedError)):
            raise Exception(
                "The exception class defined for a permission must extend "
                "either PermissionError or NotAuthenticatedError."
            )

        _has_object_permission = getattr(klass, 'has_object_permission')
        _has_permission = getattr(klass, 'has_permission')
        _user_has_permission = getattr(klass, 'has_user_permission')
        _get_permissioned_obj = getattr(klass, 'get_permissioned_obj', None)

        setattr(klass, 'has_object_permission', has_obj_permission)
        setattr(klass, 'has_permission', has_permission)
        setattr(klass, 'has_user_permission', has_user_permission)
        return klass


class BasePermission(metaclass=BasePermissionMetaclass):
    """
    Base permission class that provides the interface and common logic for
    all permissions used in the application.

    While it does not extend :obj:`rest_framework.permissions.BasePermission`
    directly, it provides all of the same behavior of the traditional
    `rest_framework` base permission class, with additional behavior provided
    either through the custom metaclass or the class itself.

    Every extension of :obj:`BasePermission` must initialize the base class with
    *all* of the arguments provided to the extension on initialization.  This
    allows us to conveniently copy the entire permission class with slightly
    different configuration values via the __call__ method:

    >>> IsFullyAuthenticated = AND(IsAuthenticated, IsActive, IsVerified)
    >>>
    >>> class View(views.GenericView):
    >>>     permission_classes = [
    >>>         IsFullyAuthenticated(priority=1),
    >>>         AnotherPermission
    >>>     ]

    Parameters:
    ----------
    get_permissioned_obj: :obj:`lambda` (optional)
        Can be either defined on the permission class statically and/or
        overridden on initialization.

        When determining if the permission class has object level permissions,
        instructs the permission class how to determine what the relevant
        object instance is based on the object instance for the detail endpoint.

        This is particularly useful when we want the permission class to apply
        to an object that is related to, but is not, the object dictated by
        the ID in the detail endpoint's PATH parameters.

        This parameter, if defined, needs to be a function taking the detail
        endpoint instance as it's first and only argument.

        Default: None

    get_nested_obj: :obj:`lambda` (optional)
        Can be either defined on the permission class statically and/or
        overridden on initialization.

        Similiar to the `get_permissioned_obj` with some very important
        differences.  As `get_permissioned_obj` applies to the permission
        methods `has_object_permission`, this method applies to the
        `has_permission` endpoint.

        This method informs the permission that even though we are not
        in a detail endpoint context, we still want to check the object level
        permissions for an object that is in the context of the view.  This
        is particularly useful when we have an endpoint that stems off of
        a detail endpoint:

        GET /budgets/<pk>/accounts/

        Here, the traditional `has_object_permission` method will not be
        triggered, since it is not a detail endpoint.  However, if we provide
        the `get_nested_obj` callback that returns the :obj:`Budget` referenced
        by the PK, the object level permissions will be checked for that
        :obj:`Budget` instance.

        This parameter, if defined, needs to be a function taking the view
        as it's first and only argument.

        Default: None

    priority: :obj:`bool` (optional)
        Whether or not the permission class should be treated with priority when
        used in a series of permission classes inside of an :obj:`Operator`
        instance.

        When an :obj:`Operator` permission check fails, the priority will help
        determine what permission the error message and code should be chosen
        from to propogate to the response.

        Permission classes are prioritized by order unless a given instance in
        the sequence sets this option to True.

        Default: False

    affects_after: :obj:`bool` (optional)
        Whether or not the permission class affects the permission classes
        defined after it when used in a series of permission classes inside of
        an :obj:`Operator` instance.

        If this value is True, and the permission fails - subsequent permissions
        in the sequence will not be evaluated and the :obj:`Operator` will use
        the failed permissions up until that point to determine the message and
        code to propogate.

        This is important when subsequent permissions depend on prior permissions
        and would throw a 500 error if the prior permissions evaluated to False.

        Default: False

    write_only_applicable: :obj:`bool` (optional)
        If True, the permission will only be evaluated for HTTP write methods
        (POST, PATCH, PUT, DELETE, etc.).

        Default: False

    read_only_applicable: :obj:`bool` (optional)
        If True, the permission will only be evaluated for HTTP safe methods
        (GET, OPTIONS, HEAD, etc.).

        Default: False

    applicable_actions: :obj:`tuple` or :obj:`list` or :obj:`str` (optional)
        An iterable of strings or a single string that define the view actions
        that the permission is applicable for.  If the incoming request is not
        associated with one of the applicable actions, the permission will not
        be evaluated.

        Default: None

    applicable_methods: :obj:`tuple` or :obj:`list` or :obj:`str` (optional)
        An iterable of strings or a single string that define the request
        methods (GET, PUT, PATCH, etc.) that the permission is applicable for.
        If the incoming request is not associated with one of the applicable
        methods, the permission will not be evaluated.

        Default: None
    """
    exception_class = PermissionError
    exception_kwargs = {}

    config = [
        PermissionConfig(
            attr='write_only_applicable',
            type=bool,
            default=False,
            conflicts=[
                'read_only_applicable',
                'applicable_actions',
                'applicable_methods'
            ]
        ),
        PermissionConfig(
            attr='read_only_applicable',
            type=bool,
            default=False,
            conflicts=[
                'write_only_applicable',
                'applicable_actions',
                'applicable_methods'
            ]
        ),
        PermissionConfig(
            attr='applicable_methods',
            type=list,
            default=None,
            conflicts=['write_only_applicable', 'read_only_applicable']
        ),
        PermissionConfig(
            attr='applicable_actions',
            type=list,
            default=None,
            conflicts=['write_only_applicable', 'read_only_applicable']
        ),
        PermissionConfig(attr='priority', type=bool, default=False),
        PermissionConfig(attr='affects_after', type=bool, default=False),
    ]

    def __init__(self, *args, **options):
        # Maintain set of arguments used to instantiate the permission class so
        # that we can reinitialize it with overridden arguments afterwards.
        self._args = list(args)
        self._kwargs = copy.deepcopy(options)

        self._get_permissioned_obj = options.get('get_permissioned_obj', None)
        self._get_nested_obj = options.get('get_nested_obj', None)

        for c in self.config:
            v = options.get(c.attr, empty)
            if v is empty:
                v = getattr(self, c.attr, empty)

            # Make sure that the permission class is not configured with
            # conflicting configuration values.
            if v is not empty and c.conflicts is not empty:
                present_conflicts = [
                    ci for ci in self.config
                    if ci.attr != c.attr and ci.attr in options
                    and ci.attr in c.conflicts
                ]
                if present_conflicts:
                    humanized = humanize_list(
                        [ci.attr for ci in present_conflicts] + [c.attr])
                    raise ValueError(
                        f"Parameters {humanized} are mutually exclusive and "
                        f"cannot all be provided to {self.__class__.__name__}"
                    )

            default_set = False
            if v is empty:
                if c.required:
                    raise ValueError(
                        f"Configuration value for attribute {c.attr} is not "
                        f"provided on initialization or statically on the "
                        "{self.__class__.__name__} class."
                    )
                elif c.default is empty:
                    raise Exception(
                        f"Configuration {c.attr} is not required but no default "
                        "is defined."
                    )
                default_set = True
                v = c.default

            if c.type is list:
                v = ensure_iterable(v, cast_none=False)
            if not default_set and c.type is not None \
                    and not isinstance(v, c.type):
                raise ValueError(
                    f"Invalid value {v} provided for configuration {c.attr}. "
                    f"Expected value of type {c.type}."
                )
            setattr(self, f'_{c.attr}', v)

    def __call__(self, **kwargs):
        """
        Returns a new instance of the same permission class with the provided
        configurations overridden on the class.
        """
        kw = copy.deepcopy(self._kwargs)
        kw.update(kwargs)
        return self.__class__(*self._args, **kw)

    def is_applicable(self, request, view):
        """
        Returns whether or not the given :obj:`BasePermission` instance is
        applicable for the provided request and view.  If the
        :obj:`BasePermission` is not applicable for the request/view, the
        :obj:`BasePermission` will not be evaluated.
        """
        if self._read_only_applicable and not request_is_safe_method(request):
            return False
        elif self._write_only_applicable \
                and not request_is_write_method(request):
            return False
        elif self._applicable_actions is not None:
            return view.action in self._applicable_actions
        elif self._applicable_methods is not None:
            return request.method.upper() in [
                m.upper() for m in self._applicable_methods]
        return True

    @property
    def exception_kwargs(self):
        return {}

    @property
    def affects_after(self):
        return self._affects_after

    @property
    def priority(self):
        return self._priority

    def permission_denied(self, message=None, **kwargs):
        exception_kwargs = {}
        if hasattr(self, 'message'):
            exception_kwargs['detail'] = self.message
        elif hasattr(self, 'code'):
            exception_kwargs['code'] = self.code

        assert isinstance(self.exception_kwargs, (dict, tuple, list)), \
            "Exception kwargs must be a dictionary or an iterable."
        if isinstance(self.exception_kwargs, dict):
            exception_kwargs.update(self.exception_kwargs)
        else:
            exception_kwargs.update(**dict(
                (k, getattr(self, k))
                for k in self.exception_kwargs
            ))
        exception_kwargs.update(**kwargs)
        if message is not None:
            kwargs['detail'] = message

        raise self.exception_class(**exception_kwargs)

    def has_user_permission(self, user):
        return True

    def has_object_permission(self, request, view, obj):
        return True

    def has_permission(self, request, view):
        return True

import copy
import functools
from rest_framework import permissions

from greenbudget.lib.utils import (
    get_string_formatted_kwargs, with_falsey_default)
from greenbudget.app.authentication.exceptions import NotAuthenticatedError

from .constants import PermissionContext
from .exceptions import PermissionErr


def with_raise_exception(func):
    """
    Allows the permission methods on a permission class to be called with a
    `raise_exception` boolean flag, that will either force a
    :obj:`PermissionErr` to be raised specific to that permission class or
    will forcefully suppress the :obj:`PermissionErr` for that permission
    class, returning the string message associated with the
    :obj:`PermissionErr` that would have otherwise be raised.
    """
    @functools.wraps(func)
    def decorated(instance, *args, **kwargs):
        raise_exception = kwargs.pop('raise_exception', True)
        try:
            evaluated = func(instance, *args, **kwargs)
        except (PermissionErr, NotAuthenticatedError) as e:
            if raise_exception is True:
                raise e
            # Make sure to return the message on the exception class such that
            # the failed permission will be treated with that same message.
            return str(e.detail)
        else:
            if evaluated is False or isinstance(evaluated, str):
                # If the permission method returns a string message, than it
                # indicates that the permission failed and the returned value
                # is the message the PermissionErr should have.
                if raise_exception:
                    if evaluated is False:
                        instance.permission_denied()
                    else:
                        instance.permission_denied(message=evaluated)
                return evaluated
            assert evaluated is True, \
                f"Unexpected type {type(evaluated)} returned from " \
                f"permission method {func.__name__}.  Expected either " \
                "a string or a boolean."
            return True
    return decorated


class BasePermissionMetaclass(permissions.BasePermissionMetaclass):
    def __new__(cls, name, bases, dct):
        def has_user_permission(original):
            @with_raise_exception
            def inner(instance, user):
                return original(instance, user)
            return inner

        def has_permission(original):
            @with_raise_exception
            def inner(instance, request, view):
                instance.guarantee_user_dependency_flags(request)

                # If the permission exposes a user permission method and this
                # method evaluates to False, do not grant permission access.
                if hasattr(instance, 'has_user_perm') \
                        and not instance.has_user_perm(request.user):
                    return False

                if instance._get_nested_obj is not None:
                    nested_parent = instance._get_nested_obj(view)
                    return instance.has_obj_perm(request, view, nested_parent)
                return original(instance, request, view)
            return inner

        def has_obj_permission(original):
            @with_raise_exception
            def inner(instance, request, view, obj):
                instance.guarantee_user_dependency_flags(request)

                # If the permission exposes a user permission method and this
                # method evaluates to False, do not grant permission access.
                if hasattr(instance, 'has_user_perm') \
                        and not instance.has_user_perm(request.user):
                    return False

                obj = instance.get_permissioned_obj(obj)
                return original(instance, request, view, obj)
            return inner

        def format_permission_message(instance, original_message):
            formatted = original_message
            fkwargs = get_string_formatted_kwargs(formatted)
            for k in fkwargs:
                fvalue = getattr(
                    instance, k, getattr(instance, f"_{k}", None))
                if fvalue is not None:
                    formatted = formatted.replace("{%s}" % k, fvalue)
            return formatted

        dct['format_permission_message'] = format_permission_message
        if 'message' in dct:
            msg = dct["message"]
            dct['message'] = property(
                lambda instance, k=msg: format_permission_message(instance, k))

        if 'has_object_permission' in dct:
            dct['has_obj_perm'] = has_obj_permission(
                dct['has_object_permission'])

        if 'has_permission' in dct:
            dct['has_perm'] = has_permission(dct['has_permission'])

        if 'has_user_permission' in dct:
            dct['has_user_perm'] = has_user_permission(
                dct['has_user_permission'])

        return super().__new__(cls, name, bases, dct)


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

    is_view_applicable: :obj:`bool` or :obj:`lambda` (optional)
        Either a boolean value or a callback that takes the view context as its
        first and only argument that is used to denote whether or not a given
        permission in an operator (AND or OR) is applicable in the view context.

        This is useful when we have situations where we do not want the
        evaluated permission to count towards the overall operand in certain
        contexts.

        Permissions that have view applicability evaluating to False will not
        have their `has_permission` methods evaluated in the given context
        inside of an operand.

        Default: True

    is_object_applicable: :obj:`bool` or :obj:`lambda` (optional)
        Either a boolean value or a callback that takes the object context as its
        first and only argument that is used to denote whether or not a given
        permission in an operator (AND or OR) is applicable in the object
        context.

        This is useful when we have situations where we do not want the
        evaluated permission to count towards the overall operand in certain
        contexts.

        Permissions that have object applicability evaluating to False will not
        have their `has_object_permission` methods evaluated in the given context
        inside of an operand.

        Default: True
    """
    exception_class = PermissionErr
    user_dependency_flags = []
    default_object_name = 'object'

    def __init__(self, *args, **options):
        # Maintain set of arguments used to instantiate the permission class so
        # that we can reinitialize it with overridden arguments afterwards.
        self._args = list(args)
        self._kwargs = copy.deepcopy(options)

        # Allow None values to be passed in and still trigger the default True
        # values.
        with_falsey = with_falsey_default(options)

        self._object_name = with_falsey.get(
            'object_name', self.default_object_name)
        self._is_view_applicable = with_falsey.get('is_view_applicable', True)
        self._is_object_applicable = with_falsey.get(
            'is_object_applicable', True)

        self._priority = options.get('priority',
            getattr(self, 'priority', False))
        self._affects_after = options.get('affects_after',
            getattr(self, 'affects_after', False))
        self._get_permissioned_obj = options.get('get_permissioned_obj')
        self._get_nested_obj = options.get('get_nested_obj', None)

    def __call__(self, **kwargs):
        """
        Returns a new instance of the same permission class with the provided
        configurations overridden on the class.
        """
        kw = copy.deepcopy(self._kwargs)
        kw.update(kwargs)
        return self.__class__(*self._args, **kw)

    def get_permissioned_obj(self, obj):
        # If the callback to get the permissioned object was provided on
        # init, it overrides the class method.
        if self._get_permissioned_obj is not None:
            return self._get_permissioned_obj(obj)
        return obj

    def is_prioritized(self, *args):
        """
        Returns whether or not the permission is prioritized for the given
        permission context, :obj:`ObjectContext` or :obj:`ViewContext`.

        When a permission is prioritized, it will be used for determining the
        specific information raised in the :obj:`PermissionErr` when it fails
        along with other permissions in a given :obj:`Operator`.
        """
        if self.priority is not None:
            if hasattr(self.priority, '__call__'):
                return self.priority(PermissionContext.from_args(*args))
            return self.priority
        return False

    def is_object_applicable(self, context):
        """
        Returns whether or not the permission is applicable for the given
        permission object context, :obj:`ObjectContext`.

        If the permission is not applicable for the given context, it will be
        excluded from the evaluation - instead of contributing a truthy value
        to the overall permission evaluation.
        """
        if isinstance(self._is_object_applicable, bool):
            return self._is_object_applicable
        return self._is_object_applicable(context)

    def is_view_applicable(self, context):
        """
        Returns whether or not the permission is applicable for the given
        permission view context, :obj:`ViewContext`.

        If the permission is not applicable for the given context, it will be
        excluded from the evaluation - instead of contributing a truthy value
        to the overall permission evaluation.
        """
        if isinstance(self._is_view_applicable, bool):
            return self._is_view_applicable
        return self._is_view_applicable(context)

    def guarantee_user_dependency_flags(self, request):
        """
        Ensures that the flags on the :obj:`User` instance, defined by the
        `user_dependency_flags` attribute, all evaluate to the desired values
        before permission checks are performed.

        This is done to ensure that certain permission classes are always
        proceeded by a permission class that guarantees the authenticity
        of the :obj:`User`.
        """
        user = request.user
        for attr in self.user_dependency_flags:
            if not getattr(user, attr):
                raise Exception(
                    f"The permission class {self.__class__.__name__} should "
                    "always be preceeded by a permission class that guarantees "
                    f"`{attr} = True` on the user."
                )

    @property
    def exception_kwargs(self):
        """
        Can be overridden by extensions of the :obj:`BasePermission` class
        such that the returned arguments are provided to the raised
        :obj:`PermissionErr` when the permission fails.
        """
        return {}

    @property
    def affects_after(self):
        """
        Returns whether or not an instance of  :obj:`BasePermission` extension
        affects other instances of :obj:`BasePermission` that occur after it
        in an :obj:`Operator`.

        If the permission affects permissions after it when used in an
        :obj:`Operator` and it fails, the permissions after it will not be
        evaluated.
        """
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
            exception_kwargs['detail'] = self.format_permission_message(message)

        raise self.exception_class(**exception_kwargs)

    def has_object_permission(self, request, view, obj):
        return True

    def has_permission(self, request, view):
        return True

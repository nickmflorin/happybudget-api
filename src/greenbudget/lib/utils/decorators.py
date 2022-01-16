import functools
import inspect
import os
import warnings


def optional_parameter_decorator(f):
    """
    A decorator for a decorator, allowing the decorator to be used both with
    and without arguments applied.

    Example:
    ------
    @optional_parameter_decorator
    def decorator(func, foo='bar'):
        pass

    which can now be used as

    @decorator
    def my_method():
        pass

    or

    @decorator(foo='foo')
    def my_method():
        pass
    """
    @functools.wraps(f)
    def wrapped_decorator(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # Return the actual decorated function.
            return f(args[0])
        else:
            # Wrap the function in a decorator in the case that arguments are
            # applied.
            return lambda realf: f(realf, *args, **kwargs)
    return wrapped_decorator


def deprecated(*args, alternate=None, reason=None):
    """
    A decorator to flag a method or class as deprecated and issue a
    DeprecationWarning if it is used.  If the `alternate` argument is supplied,
    the warning will indicate that the user should use the alternate method.

    Usage:
    -----
    (1) Decorating a class without configuration parameters:

    >>> @deprecated
    >>> class MyClass:
    >>>     pass

    (2) Decorating a class with configuration parameters:

    >>> @deprecated(alternate="MyNewClass")
    >>> class MyClass:
    >>>     pass

    (3) Decorating a function without configuration parameters:

    >>> @deprecate
    >>> def my_function():
    >>>     pass

    (4) Decorating a function with configuration parameters:

    >>> @deprecated(alternate="my_new_function")
    >>> def my_function():
    >>>     pass
    """
    def warn(obj):
        reference = "class" if inspect.isclass(obj) else "method"
        parts = ["The %s %s is deprecated." % (reference, obj.__name__)]
        if alternate is not None:
            if not isinstance(alternate, str):
                parts.append("Please use %s instead." % alternate.__name__)
            else:
                parts.append("Please use %s instead." % alternate)
        if reason is not None:
            parts.append("Reason: %s" % reason)
        print("DeprecationWarning: %s" % " ".join(parts))
        warnings.warn(" ".join(parts), DeprecationWarning)

    def decorate(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            warn(func)
            return func(*args, **kwargs)
        return inner

    # If arguments are supplied, either as a class or a function, then no
    # configuration parameters are provided.
    if len(args) == 1:
        if inspect.isclass(args[0]):
            klass = args[0]
            env_key = '__deprecation_warning_%s_issued__' % klass.__name__
            os.environ.setdefault(env_key, "0")

            if os.environ[env_key] == "0":
                # If the argument is a class, simply issue the warning once so
                # the warning is not issued everytime the class is initialized,
                # and return the unmanipulated class.
                warn(klass)
                # Set environment variable so that we do not issue multiple
                # warnings for same class on startup.
                os.environ[env_key] = "1"
            return klass
        else:
            # If the argument is a function, wrap the function in a decorator
            # such that the warning is issued when the function is called.
            assert hasattr(args[0], '__call__'), \
                "Invalid usage of decorator."
            return decorate(args[0])

    # At this point, we know that configuration parameters were provided.
    return functools.partial(deprecated, alternate=alternate, reason=reason)

import functools
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

    @decorator(foo='bar')
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


@optional_parameter_decorator
def deprecated(func, alternate=None, reason=None):
    """
    A decorator to flag a method as deprecated and issue a DeprecationWarning
    if it is used.  If the `alternate` argument is supplied, the warning will
    indicate that the user should use the alternate method.

    Args:
        alternate
            Either a function object or a string name of an alternate method
            that can be used.
    """
    @functools.wraps(func)
    def inner(*args, **kwargs):
        parts = ["The method %s is deprecated." % func.__name__]

        if alternate is not None:
            if not isinstance(alternate, str):
                parts.append("Please use %s instead." % alternate.__name__)
            else:
                parts.append("Please use %s instead." % alternate)

        if reason is not None:
            parts.append("Reason: %s" % reason)
        warnings.warn(" ".join(parts), DeprecationWarning)
        return func(*args, **kwargs)

    return inner

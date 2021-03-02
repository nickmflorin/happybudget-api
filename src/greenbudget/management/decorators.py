import functools

from django.conf import settings
from django.core import management


def debug_only(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        if not settings.DEBUG:
            raise management.base.CommandError(
                "This command cannot be run in production.")
        return func(*args, **kwargs)
    return inner


def skippable(*prompts, argument=None):
    """
    Decorator to allow a method on the :obj:`CustomCommand` to be
    skipped.

    Parameters:
    ----------
    prompts: :obj:iter
        A series of prompts to display to the user when the method is being
        skipped.

    argument: :obj:`str`
        By default, the management command argument to indicate that the method
        should be skipped will be `skip_<func_name>`.  If the argument should
        be different, it can be explicitly provided here.
    """
    def decorator(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            parameter = argument or "skip_%s" % func.__name__
            if parameter in kwargs and kwargs[parameter] is True:
                instance.prompt(*prompts,
                    style_func=instance.style.HTTP_NOT_MODIFIED)
                return False
            else:
                return func(instance, *args, **kwargs)
        return inner
    return decorator


def askable(*prompts):
    """
    Decorator to ask the user if they want to perform a certain operation
    before the method proceeds.

    Parameters:
    ----------
    prompts: :obj:iter
        A series of prompts to display to the user when asking if they want
        to skip the operation.
    """
    def decorator(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            if "ask" in kwargs and kwargs["ask"] is False:
                return func(instance, *args, **kwargs)
            instance.prompt(*prompts)
            if instance.query_boolean():
                return func(instance, *args, **kwargs)
        return inner
    return decorator

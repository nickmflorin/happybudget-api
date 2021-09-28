import functools

from django.conf import settings
from django.core import management


def debug_only(cls):
    def add_arguments(instance, parser):
        cls.__original_add_arguments__(instance, parser)
        parser.add_argument(
            '--force_prod',
            action='store_true',
            help='Force the command to run in production.',
        )

    def handle(instance, *args, **kwargs):
        if not settings.DEBUG:
            if kwargs['force_prod'] is False:
                raise management.base.CommandError(
                    "This command cannot be run in production.")
            else:
                instance.warning(
                    "You are about to run a debug only command in production, "
                    "please make sure this is safe to do before continuing..."
                )
                if instance.query_boolean(prompt="Would you like to continue?"):
                    return cls.__original_handle__(instance, *args, **kwargs)
                else:
                    instance.info("Aborting...")
        else:
            return cls.__original_handle__(instance, *args, **kwargs)

    cls.__original_handle__ = cls.handle
    cls.__original_add_arguments__ = cls.add_arguments

    cls.add_arguments = add_arguments
    cls.handle = handle

    return cls


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

import functools
import logging

from django import dispatch
from django.db import models

from greenbudget.lib.utils import ensure_iterable
from greenbudget.lib.utils.decorators import optional_parameter_decorator

from .signals import (
    post_create, any_fields_changed_signal, field_changed_signal,
    post_save, m2m_changed, post_delete, pre_delete, pre_save)


logger = logging.getLogger('signals')


@optional_parameter_decorator
def suppress_signal(func, params=None):

    def validate_param(param):
        if isinstance(param, str):
            return True
        if isinstance(param, (list, tuple)) and len(param) == 2:
            return True
        raise Exception(
            "The param to suppress a signal must be a string attribute or a "
            "length-2 tuple/list of a string attribute - expected value pair."
        )

    params = ensure_iterable(params) + ['suppress_signals']
    [validate_param(p) for p in params]

    def get_param_name(param):
        if isinstance(param, str):
            return param
        return param[0]

    def has_param_value(instance, param):
        return hasattr(instance, '_%s' % get_param_name(param))

    def get_param_value(instance, param):
        return instance.get_flag(get_param_name(param))

    def param_indicates_suppress(instance, param):
        value = get_param_value(instance, param)
        if isinstance(param, str):
            return value is True
        return value is param[1]

    @functools.wraps(func)
    def decorated(instance, *args, **kwargs):
        if not hasattr(instance, '__decorated_for_signals__'):
            raise Exception(
                "Model %s is not decorated for signals." % type(instance).__name__)  # noqa
        for param in params:
            if has_param_value(instance, param) \
                    and param_indicates_suppress(instance, param):
                logger.info(
                    "Suppressing receiver {func} due to {param} = {value}".format(  # noqa
                        func=func.__name__,
                        param=get_param_name(param),
                        value=get_param_value(instance, param)
                    )
                )
                return
        return func(instance, *args, **kwargs)
    return decorated


def any_fields_changed_receiver(fields, **kwargs):
    signal = any_fields_changed_signal(fields, **kwargs)
    return dispatch.receiver(signal, **kwargs)


def field_changed_receiver(field, **kwargs):
    signal = field_changed_signal(field, **kwargs)

    def decorator(func):
        signal.connect(func, weak=False)
        return func
    return decorator


@dispatch.receiver(models.signals.post_save)
def handle_universal_post_save(instance, sender, signal, **kwargs):
    if sender.__module__.startswith("greenbudget.app"):
        if kwargs['created'] is True:
            post_create.send(sender, instance=instance, **kwargs)
        post_save.send(sender, instance=instance, **kwargs)


@dispatch.receiver(models.signals.m2m_changed)
def handle_universal_m2m_changed(signal, **kwargs):
    m2m_changed.send(**kwargs)


@dispatch.receiver(models.signals.post_delete)
def handle_universal_post_delete(signal, **kwargs):
    post_delete.send(**kwargs)


@dispatch.receiver(models.signals.pre_delete)
def handle_universal_pre_delete(signal, **kwargs):
    pre_delete.send(**kwargs)


@dispatch.receiver(models.signals.pre_save)
def handle_universal_pre_save(signal, **kwargs):
    pre_save.send(**kwargs)

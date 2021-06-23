import functools
import logging

from django import dispatch
from django.db import models

from greenbudget.lib.utils.decorators import optional_parameter_decorator

from .signals import (
    post_create, any_fields_changed_signal, field_changed_signal)


logger = logging.getLogger('signals')


@optional_parameter_decorator
def suppress_signal(func, params=None):

    def evaluate_param(instance, param):
        if isinstance(param, str):
            return getattr(instance, '_%s' % param, False) is True
        assert isinstance(param, (list, tuple)) and len(param) == 2, \
            "Suppress signal params must be a string attribute or a " \
            "tuple/list of string attribute - expected value pair."
        return getattr(instance, '_%s' % param[0], None) == param[1]

    @functools.wraps(func)
    def decorated(instance, *args, **kwargs):
        if getattr(instance, '_suppress_signals', False) is True:
            return
        elif params is not None and any([
                evaluate_param(instance, k) for k in params]):
            return
        return func(instance, *args, **kwargs)
    return decorated


def any_fields_changed_receiver(fields, **kwargs):
    signal = any_fields_changed_signal(fields, **kwargs)

    def decorator(func):
        signal.connect(func, weak=False)
        return func
    return decorator


def field_changed_receiver(field, **kwargs):
    signal = field_changed_signal(field, **kwargs)

    def decorator(func):
        signal.connect(func, weak=False)
        return func
    return decorator


@dispatch.receiver(models.signals.post_save)
def handle_universal_post_save(instance, **kwargs):
    if kwargs['sender'].__module__.startswith("greenbudget.app"):
        if kwargs['created'] is True:
            post_create.redirect(instance, **kwargs)

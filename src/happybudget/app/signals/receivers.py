from django import dispatch
from django.db import models

from .signals import (
    post_create, field_changed_signal, post_save, m2m_changed, post_delete,
    pre_delete, pre_save, any_fields_changed_signal)


def any_fields_changed_receiver(fields, **kwargs):
    signal = any_fields_changed_signal(fields, **kwargs)
    return dispatch.receiver(signal, **kwargs)


def field_changed_receiver(field, **kwargs):
    signal = field_changed_signal(field, **kwargs)
    return dispatch.receiver(signal, **kwargs)


@dispatch.receiver(models.signals.post_save)
def handle_universal_post_save(instance, sender, signal, **kwargs):
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

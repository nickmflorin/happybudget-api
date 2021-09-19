from greenbudget.lib.utils import ensure_iterable

from .signal import Signal


post_create = Signal(name='post_create')
post_save = Signal(name='post_save')
post_create_by_user = Signal(name='post_create_by_user')
field_changed = Signal(name='field_changed')
fields_changed = Signal(name='fields_changed')
m2m_changed = Signal(name='m2m_changed')
post_delete = Signal(name='post_delete')
pre_delete = Signal(name='pre_delete')
pre_save = Signal(name='pre_save')


def any_fields_changed_signal(fields, **kwargs):
    fields = ensure_iterable(fields)
    temp_signal = Signal(add_to_registry=False)

    def field_receiver(instance, sender, signal, **kw):
        changed_fields = [change.field for change in kw['changes']]
        if any([f in changed_fields for f in fields]):
            temp_signal.send(
                instance=instance,
                sender=type(instance),
                **kw
            )

    fields_changed.connect(field_receiver, weak=False, **kwargs)
    return temp_signal


def field_changed_signal(field, **kwargs):
    temp_signal = Signal(add_to_registry=False)

    def field_receiver(instance, sender, signal, **kw):
        if kw['change'].field == field:
            temp_signal.send(
                instance=instance,
                sender=type(instance),
                **kw
            )

    field_changed.connect(field_receiver, weak=False, **kwargs)
    return temp_signal

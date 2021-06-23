from greenbudget.lib.utils import ensure_iterable

from .signal import Signal


post_create = Signal()
post_create_by_user = Signal()
field_changed = Signal()
fields_changed = Signal()


def any_fields_changed_signal(fields, **kwargs):
    fields = ensure_iterable(fields)
    temp_signal = Signal()

    def field_receiver(instance, **kw):
        changed_fields = [change.field for change in kw['changes']]
        if any([f in changed_fields for f in fields]):
            temp_signal.redirect(instance, **kw)

    fields_changed.connect(field_receiver, weak=False, **kwargs)
    return temp_signal


def field_changed_signal(field, **kwargs):
    temp_signal = Signal()

    def field_receiver(instance, **kw):
        if kw['change'].field == field:
            temp_signal.redirect(instance, **kw)

    field_changed.connect(field_receiver, weak=False, **kwargs)
    return temp_signal

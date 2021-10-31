import contextlib
import functools

from django import dispatch


class Registry:
    def __init__(self, signals=None):
        self._signals = signals or []

    @property
    def signals(self):
        return self._signals

    def add(self, signal):
        if signal.name is None:
            raise Exception(
                "A signal must be provided a name to be added to the "
                "internal registry."
            )
        elif signal.name in [sig.name for sig in self._signals]:
            raise Exception(
                "Cannot register multiple signals with the same name.")
        self._signals.append(signal)

    def get_signal(self, name):
        if name not in [sig.name for sig in self._signals]:
            raise LookupError("No registered signal with name %s." % name)
        return [sig for sig in self._signals if sig.name == name][0]


registry = Registry()


class Signal(dispatch.Signal):
    def __init__(self, name=None, use_caching=False, disabled=False,
            add_to_registry=True):
        super().__init__(use_caching=use_caching)
        self.name = name
        self._add_to_registry = add_to_registry
        self._disabled = disabled
        if self._add_to_registry is True:
            registry.add(self)

    @contextlib.contextmanager
    def _disable(self, sender=None):
        self._disabled = sender if sender is not None else True
        try:
            yield self
        finally:
            self._disabled = False

    def disabled(self, sender):
        if type(self._disabled) is bool:
            return self._disabled
        return sender is self._disabled

    def disable(self, *args, **kwargs):
        sender = kwargs.pop('sender', None)
        if len(args) == 1 and hasattr(args[0], '__call__'):
            func = args[0]

            @functools.wraps(func)
            def decorated(*args, **kwargs):
                with self._disable(sender=sender):
                    return func(*args, **kwargs)
            return decorated
        return self._disable(sender=sender)

    def send(self, sender, **named):
        if self.disabled(sender):
            return
        return super().send(sender, **named)


@contextlib.contextmanager
def disable(signals=None):
    signals = signals or registry.signals
    disabled_signals = []
    for signal in signals:
        if isinstance(signal, str):
            signal = registry.get_signal(signal)
        disabled_signals.append(signal)
        signal._disabled = True
    try:
        yield
    finally:
        for signal in disabled_signals:
            signal._disabled = False

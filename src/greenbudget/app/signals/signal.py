import contextlib
import functools

from django import dispatch


class Signal(dispatch.Signal):
    def __init__(self, use_caching=False, disabled=False):
        super().__init__(use_caching=use_caching)
        self._disabled = disabled

    @contextlib.contextmanager
    def _disable(self):
        self._disabled = True
        try:
            yield self
        finally:
            self._disabled = False

    def disable(self, *args):
        if len(args) == 1 and hasattr(args[0], '__call__'):
            func = args[0]

            @functools.wraps(func)
            def decorated(*args, **kwargs):
                with self._disable():
                    return func(*args, **kwargs)
            return decorated
        return self._disable()

    def send(self, sender, **named):
        if self._disabled:
            return
        return super().send(sender, **named)


@contextlib.contextmanager
def disable(signals):
    for signal in signals:
        signal._disabled = True
    try:
        yield
    finally:
        for signal in signals:
            signal._disabled = False

import contextlib

from django import dispatch


class Signal(dispatch.Signal):
    def __init__(self, use_caching=False, disabled=False):
        super().__init__(use_caching=use_caching)
        self._disabled = disabled

    @contextlib.contextmanager
    def disable(self):
        self._disabled = True
        try:
            yield self
        finally:
            self._disabled = False

    def send(self, sender, **named):
        if self._disabled:
            return
        return super().send(sender, **named)

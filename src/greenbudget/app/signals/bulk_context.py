import functools
import threading

from django.db import transaction


class FuncSignature:
    def __init__(self, func, args=None, kwargs=None, id=None):
        self.func = func
        self.args = tuple(args or [])
        self.kwargs = dict(kwargs or {})
        self.id = id

    def __call__(self):
        return self.func(*self.args, **self.kwargs)

    def __eq__(self, other):
        if self.id is not None:
            return hash(self.func) == hash(other.func) and self.id == other.id
        return hash(self.func) == hash(other.func) \
            and self.args == other.args \
            and self.kwargs == other.kwargs


class bulk_context_manager(threading.local):
    def __init__(self, active=False):
        super().__init__()
        self.queue = []
        self._active = active
        self._flushing = False

    @property
    def active(self):
        return self._active

    def __call__(self, f):
        @functools.wraps(f)
        def decorated(*args, **kwds):
            with self:
                return f(*args, **kwds)
        return decorated

    def __enter__(self):
        if self._active is True:
            return self
        with transaction.atomic():
            self._active = True
            return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not exc_type:
            self.flush()
        self._active = False
        return False

    def flush(self):
        while self.queue:
            queue = self.queue[:]
            self.queue = []
            for signature in queue:
                signature()

    def decorate(self, recall_id=None):
        def decorator(func):
            @functools.wraps(func)
            def decorated(*args, **kwargs):
                if self._active is False:
                    return func(*args, **kwargs)

                explicit_id = None
                if recall_id is not None:
                    explicit_id = recall_id(*args, **kwargs)

                signature = FuncSignature(func, args, kwargs, id=explicit_id)
                if signature not in self.queue:
                    self.queue.append(signature)
            return decorated
        return decorator


bulk_context = bulk_context_manager()

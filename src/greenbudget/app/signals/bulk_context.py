import functools
import logging
import threading

from django.db import transaction

from greenbudget.lib.utils import ensure_iterable


logger = logging.getLogger('signals')


def name_if_obj(obj):
    if hasattr(obj, '__name__'):
        return obj.__name__
    return obj


def lazy_caller(caller=None):
    def caller(f, args=None, kwargs=None):
        args = args or ()
        kwargs = kwargs or {}
        kwargs['caller'] = caller
        return f(*args, **kwargs)
    return caller


class FunctionSignature:
    def __init__(self, context, func, args=None, kwargs=None, id=None,
            bind=False, caller=None):
        self.context = context
        self.func = func
        self.args = tuple(args or [])
        self.kwargs = dict(kwargs or {})
        self.id = id
        self.bind = bind
        self.caller = [c for c in ensure_iterable(caller) if c is not None]

    def __call__(self):
        if self.bind is True:
            return self.func(self.context, *self.args, **self.kwargs)
        return self.func(*self.args, **self.kwargs)

    def __eq__(self, other):
        if self.id is not None:
            return hash(self.func) == hash(other.func) and self.id == other.id
        return hash(self.func) == hash(other.func) \
            and self.args == other.args \
            and self.kwargs == other.kwargs

    @property
    def callers_string(self):
        if not self.caller:
            return None
        return [name_if_obj(c) for c in self.caller]

    @property
    def func_string(self):
        return name_if_obj(self.func)

    def __str__(self):
        attributes = [
            ('func_string', 'func'),
            ('callers_string', 'callers'),
            'args',
            'kwargs'
        ]
        if self.id is not None:
            attributes = attributes[:2] + ['id']

        string_parts = [
            "{attr}={value}".format(
                attr=attr[1] if isinstance(attr, tuple) else attr,
                value=getattr(self, attr[0] if isinstance(attr, tuple) else attr)  # noqa
            )
            for attr in attributes
            if getattr(self, attr[0] if isinstance(attr, tuple) else attr) is not None  # noqa
        ]
        return "Signature(%s)" % ", ".join(string_parts)


class bulk_context_manager(threading.local):
    def __init__(self, active=False):
        super().__init__()
        self.queue = []
        self.lazy_saves = []
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
        logger.info("Entering bulk context.")
        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        logger.info(
            "Exiting bulk context, queue length = %s." % len(self.queue))
        if not exc_type:
            with transaction.atomic():
                self.flush()
        self._active = False
        return False

    def flush(self):
        while self.queue:
            level_queue = self.queue[:]
            for signature in level_queue:
                logger.info("Flushing: %s" % signature)
                signature()
            # Wait until after all of the signatures are called before
            # removing them from the queue.  Calling a signature might result
            # in an additional signature being added to the queue, and we still
            # do not want to add that signature if it was already in the queue
            # to begin with.
            for signature in level_queue:
                self.queue.remove(signature)

    def handler(self, recall_id=None, bind=False, queue_in_context=False):
        def decorator(func):
            @functools.wraps(func)
            def decorated(*args, **kwargs):
                root_caller = kwargs.pop('caller', [])

                if self._active is False or queue_in_context is False:
                    if bind:
                        setattr(self, 'call', lazy_caller([root_caller, func]))
                        return func(self, *args, **kwargs)
                    return func(*args, **kwargs)

                explicit_id = None
                if recall_id is not None:
                    explicit_id = recall_id(*args, **kwargs)

                signature = FunctionSignature(
                    context=self,
                    bind=bind,
                    func=func,
                    caller=root_caller,
                    args=args,
                    kwargs=kwargs,
                    id=explicit_id
                )
                if signature not in self.queue:
                    logger.info("Adding Signature to Queue: %s" % signature)
                    self.queue.append(signature)
                else:
                    logger.debug("Ignoring repetitive call to %s." % signature)
            return decorated
        return decorator


bulk_context = bulk_context_manager()

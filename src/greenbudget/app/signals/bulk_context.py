import functools
import logging
import inspect
import threading

from django.db import transaction

from greenbudget.lib.utils import ensure_iterable, get_function_keyword_defaults


logger = logging.getLogger('signals')


class SideEffect:
    def __init__(self, func, id=None, args=None, kwargs=None, conditional=None,
            children=None):
        self._id = id
        self.func = func
        self.args = tuple(args or [])
        self.kwargs = dict(kwargs or {})
        self.conditional = conditional

        self.children = children

    def __call__(self, context):
        result = self.call_func(self.func)
        queue_in_context = getattr(self.func, '__options__')['queue_in_context']
        # If we are not in an active bulk context, then we need to also call
        # the function side effects immediately.
        if context.active is False or queue_in_context is False:
            side_effects = self._get_children_side_effects(self)
            for effect in side_effects:
                effect(context)
        return result

    def __str__(self):
        return '%s-%s' % (self.func.__name__, self._id)

    def bind(self, parent):
        self._id = self._id or parent._id

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, value):
        self._children = ensure_iterable(value or [])
        [child.bind(self) for child in self._children]

    @property
    def id(self):
        assert self._id is not None
        return '%s-%s' % (hash(self.func), self._id)

    def call_func(self, func):
        return func(*self.args, **self.kwargs)

    def evaluate_conditional(self):
        if self.conditional is not None:
            conditional = self.conditional
            assert isinstance(conditional, bool), \
                "The conditional for a side effect must be a boolean or " \
                "return a boolean."
            return conditional
        return True

    def _get_children_side_effects(self, base_effect):
        if base_effect.children is not None:
            side_effects = ensure_iterable(base_effect.children)
            return [
                effect for effect in side_effects
                if effect.evaluate_conditional() is True
            ]
        return []

    def get_all_side_effects(self):
        def get_func_side_effects(effect):
            side_effects = self._get_children_side_effects(effect)
            effects = []
            for effect in side_effects:
                effects.append(effect)
                nested_effects = get_func_side_effects(effect)
                effects.extend(nested_effects)
            return effects

        return get_func_side_effects(self)


class bulk_context_manager(threading.local):
    def __init__(self, active=False):
        super().__init__()
        self.queue = {}
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
        # Keep flushing until queue empty.  It is possible that calling other
        # signatures results in the queue increasing in size.
        while self.queue:
            # Collect Side Effects - We want to do this first, because we want
            # the arguments supplied to the side effect to be the same at the
            # time of the call.
            flattened_queue = {}
            for id, signature in self.queue.items():
                flattened_queue[id] = signature
                for effect in signature.get_all_side_effects():
                    flattened_queue[effect.id] = effect

            # Now that we have collected all the signatures and nested side
            # effects in the queue, we can clear the queue - calling the
            # signatures and side effects may result in the context's queue
            # increasing in size again.
            self.queue = {}

            # Call all the queued signatures and side effects.
            for id, signature in flattened_queue.items():
                logger.info("Flushing: %s" % signature)
                signature(self)

    def call_in_queue(self, func):
        def use_callback(f, *a, **kw):
            handler_argspec = inspect.getargspec(func)
            callback_argspec = inspect.getargspec(f)

            keyword_args = {}
            defaults = get_function_keyword_defaults(func)
            for arg_name in callback_argspec.args:
                try:
                    keyword_args[arg_name] = [
                        v for i, v in enumerate(a)
                        if handler_argspec.args[i] == arg_name
                    ][0]
                except IndexError:
                    keyword_args[arg_name] = kw.get(arg_name, defaults[arg_name])
                except KeyError:
                    raise TypeError(
                        "The callback %s expects an argument for %s, but "
                        "this argument is not passed into the handler method."
                        % (f.__name__, arg_name)
                    )
            return f(**keyword_args)

        def caller(*args, **kwargs):
            conditional = kwargs.pop('conditional', None) \
                or getattr(func, '__options__')['conditional']
            if conditional is not None:
                if hasattr(conditional, '__call__'):
                    conditional = use_callback(conditional, *args, **kwargs)

            # If the conditional evaluates to False, do not proceed with any
            # step (even getting the ID) as the ID callback might require state
            # that is guarded against with the conditional.
            if conditional is False:
                return

            id = kwargs.pop('id', None) or getattr(func, '__options__')['id']
            if hasattr(id, '__call__'):
                id = use_callback(id, *args, **kwargs)

            side_effects = getattr(func, '__options__')['side_effect']
            if hasattr(side_effects, '__call__'):
                side_effects = use_callback(side_effects, *args, **kwargs)

            signature = SideEffect(
                id=id,
                func=func,
                args=args,
                kwargs=kwargs,
                children=side_effects
            )
            queue_in_context = getattr(func, '__options__')['queue_in_context']
            if self._active is False or queue_in_context is False:
                signature(self)
            else:
                # Always use most up to date signature.
                self.queue[signature.id] = signature
        return caller

    def handler(self, id, queue_in_context=False, side_effect=None,
            conditional=None):
        def decorator(func):
            setattr(func, '__options__', {
                'id': id,
                'queue_in_context': queue_in_context,
                'side_effect': side_effect,
                'conditional': conditional,
            })
            setattr(func, 'call_in_queue', self.call_in_queue(func))

            @functools.wraps(func)
            def decorated(*args, **kwargs):
                func.call_in_queue(*args, **kwargs)
            return decorated
        return decorator


bulk_context = bulk_context_manager()

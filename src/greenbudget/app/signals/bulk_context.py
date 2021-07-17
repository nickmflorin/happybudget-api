import functools
import logging
import threading

from django.db import transaction

from greenbudget.lib.utils import ensure_iterable


logger = logging.getLogger('signals')


class SideEffect:
    def __init__(self, func, args=None, kwargs=None, conditional=None):
        self.func = func
        self.args = tuple(args or [])
        self.kwargs = dict(kwargs or {})
        self.conditional = conditional

    def __call__(self, context):
        result = self.call_func(self.func)
        queue_in_context = getattr(self.func, '__options__')['queue_in_context']
        # If we are not in an active bulk context, then we need to also call
        # the function side effects immediately.
        if context.active is False or queue_in_context is False:
            side_effects = self._get_function_side_effects()
            for effect in side_effects:
                effect(context)
        return result

    def call_func(self, func):
        return func(*self.args, **self.kwargs)

    @property
    def id(self):
        func_id = getattr(self.func, '__options__')['id']
        if hasattr(func_id, '__call__'):
            func_id = self.call_func(func_id)
        return '%s-%s' % (hash(self.func), func_id)

    def _evaluate_side_effect_conditional(self, side_effect, parent=None):
        parent = parent or self
        if side_effect.conditional is not None:
            conditional = side_effect.conditional
            if hasattr(conditional, '__call__'):
                conditional = parent.call_func(conditional)
            assert isinstance(conditional, bool), \
                "The conditional for a side effect must be a boolean or " \
                "return a boolean."
            return conditional
        return True

    def _get_function_side_effects(self, func=None, parent=None):
        parent = parent or self
        func = func or self.func
        side_effects = getattr(func, '__options__')['side_effect']
        if side_effects is not None:
            if hasattr(side_effects, '__call__'):
                side_effects = parent.call_func(side_effects)
            side_effects = ensure_iterable(side_effects)
            return [
                effect for effect in side_effects
                if self._evaluate_side_effect_conditional(effect, parent) is True  # noqa
            ]
        return []

    def get_all_side_effects(self):
        def get_func_side_effects(func, parent):
            side_effects = self._get_function_side_effects(
                func=func, parent=parent)

            effects = []
            for effect in side_effects:
                effects.append(effect)
                nested_effects = get_func_side_effects(effect.func, effect)
                effects.extend(nested_effects)
            return effects

        return get_func_side_effects(self.func, self)


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
        def caller(*args, **kwargs):
            conditional = kwargs.pop('conditional', None) \
                or getattr(func, '__options__')['conditional']

            if conditional is not None:
                if hasattr(conditional, '__call__'):
                    conditional = conditional(*args, **kwargs)

            # If the conditional evaluates to False, do not proceed with any
            # step (even getting the ID) as the ID callback might require state
            # that is guarded against with the conditional.
            if conditional is False:
                return

            id = kwargs.pop('id', None) or getattr(func, '__options__')['id']
            if hasattr(id, '__call__'):
                id = id(*args, **kwargs)

            signature = SideEffect(
                func=func,
                args=args,
                kwargs=kwargs
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

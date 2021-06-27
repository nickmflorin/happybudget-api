from greenbudget.lib.utils import ensure_iterable


class model:
    """
    A common decorator for all of our applications :obj:`django.db.models.Model`
    instances.  All :obj:`django.db.models.Model` instances that have connected
    signals should be decorated with this class.
    """

    def __init__(self, flags=None):
        self._flags = ensure_iterable(flags)

    def __call__(self, cls):
        def save(instance, *args, **kwargs):
            """
            Overrides the :obj:`django.db.models.Model` save behavior to
            attach certain flags on the model that can be used for reference
            in save related signals.
            """
            for flag in self._flags:
                if flag in kwargs:
                    setattr(instance, '_%s' % flag, kwargs.pop(flag))

            save._original(instance, *args, **kwargs)

        # Replace the model save method with the overridden one, but keep track
        # of the original save method so it can be reapplied.
        save._original = cls.save
        cls.save = save

        # Track that the model was decorated with this class for purposes of
        # model inheritance and/or prevention of model inheritance.
        setattr(cls, '__decorated_for_signals__', self)

        return cls

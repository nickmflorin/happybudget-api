class flag_model:
    """
    Allows flags to be set on model instances during save for purposes of
    context in save related signals.
    """

    def __init__(self, *flags):
        self._flags = list(flags)

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
        setattr(cls, '__flag_model_decorated__', self)

        return cls

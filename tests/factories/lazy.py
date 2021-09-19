class Lazy:
    def __init__(self, factory_fn, **lazy_kwargs):
        self._factory_fn = factory_fn
        self._lazy_kwargs = lazy_kwargs

    def create(self, **kwargs):
        return self._factory_fn(**self._lazy_kwargs, **kwargs)

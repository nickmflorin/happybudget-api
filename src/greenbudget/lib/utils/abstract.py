import collections

from .builtins import ensure_iterable


class ImmutableSequence(collections.abc.Sequence):
    """
    An immutable sequence class that can be extended to behave like an iterable
    but implement additional functionality.
    """

    def __init__(self, data):
        self._store = ensure_iterable(data, cast=list)

    def __len__(self):
        return len(self._store)

    def __getitem__(self, index):
        return self._store.__getitem__(index)


class ImmutableAttributeMapping(collections.abc.Mapping):
    """
    An immutable mapping class that allows for attribute lookup and cacheing.
    """
    allow_caching = False

    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)
        self._cache = {}

    def transform_value(self, v):
        return v

    @property
    def data(self):
        return self._store

    def __getitem__(self, k):
        if k in self._cache:
            return self._cache[k]
        v = self.transform_value(self._store[k])
        if self.allow_caching:
            self._cache[k] = v
        return v

    def __getattr__(self, k):
        return self.__getitem__(k)

    def __iter__(self):
        return self._store.__iter__()

    def __len__(self):
        return self._store.__len__()

    def __repr__(self):
        return self._store.__repr__()

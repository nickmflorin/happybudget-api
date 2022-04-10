import collections


class ImmutableSequence(collections.abc.Sequence):
    def __init__(self, *args):
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            self._store = args[0]
        else:
            self._store = list(args)

    def __getitem__(self, i):
        return self._store[i]

    def __len__(self):
        return len(self._store)


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

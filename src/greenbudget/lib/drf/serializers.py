import collections
from rest_framework import serializers

from greenbudget.lib.utils import import_at_module_path


class ContextFieldLookupError(LookupError):
    def __init__(self, field, ref=None):
        self._field = field
        self._ref = ref

    def __str__(self):
        if self._ref is None:
            return (
                f"The field {self._field} was expected in the context but is "
                "missing."
            )
        return (
            f"The field {self._field} was expected in the context for "
            f"{self._ref} but is missing."
        )


class LazyContext(collections.abc.MutableMapping):
    """
    A mapping object that wraps a serializer's context such that a more helpful
    error is raised when accessing an element of the context that is required
    but does not exist.

    This is useful for including serializer context in callback functions
    where we expect the values to be in the context but if they are not we
    need to be aware of that.
    """

    def __init__(self, obj, ref=None):
        self._ref = ref
        self._data = obj
        if isinstance(obj, (serializers.Serializer, serializers.Field)):
            self._data = getattr(obj, 'context')
            self._ref = self._ref or type(obj).__name__

    def __iter__(self):
        return self._data.__iter__()

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError as e:
            raise ContextFieldLookupError(attr, ref=self._ref) from e

    def __getitem__(self, attr):
        return self._data.__getitem__(attr)

    def __setitem__(self, attr, v):
        return self._data.__setitem__(attr, v)

    def __len__(self):
        return self._data.__len__()

    def __delitem__(self, k):
        return self._data.__delitem__(k)

    def update(self, *args):
        return self._data.update(*args)


class PolymorphicNonPolymorphicSerializer(serializers.Serializer):
    """
    A :obj:`rest_framework.serializers.Serializer` uses different serializers
    depending on the instance being serialized.

    The name of this :obj:`rest_framework.serializers.Serializer` is not a joke.
    Typically, with Polymorphic serializers, the serializer will serialize
    based on the type of instance where each instance that it can serialize
    must be a child of a PolymorphicModel.  Here, we loosen that requirement,
    and allow the serializer to conditionally serialize an instance where that
    instance need not be a child of a Polymorphic model.
    """

    def _configure_serializer_cls(self, value):
        if isinstance(value, str):
            cls = import_at_module_path(value)
            return self._configure_serializer_cls(cls)
        assert issubclass(value, serializers.BaseSerializer), (
            "%s is not a serializer class or a module path to a serializer "
            "class." % value)
        return value

    def _find_config_for_instance(self, instance):
        if not hasattr(self, "choices"):
            raise Exception(
                "Extensions of PolymorphicNonPolymorphicSerializer must define "
                "a Meta attribute on the serializer with a `choices` attribute."
            )
        for k, v in self.choices.items():
            if isinstance(instance, k):
                return v
        raise Exception(
            "PolymorphicNonPolymorphicSerializer not configured to "
            "serialize type %s." % type(instance)
        )

    def to_representation(self, instance):
        config = self._find_config_for_instance(instance)

        options = {}
        if isinstance(config, (list, tuple)):
            if len(config) not in (1, 2):
                raise Exception("Invalid choice provided.")
            serializer_cls = self._configure_serializer_cls(config[0])
            if len(config) == 2:
                assert type(config[1]) is dict, \
                    "Serializer keyword arguments must be a dict."
                options = config[1]
        else:
            serializer_cls = self._configure_serializer_cls(config)

        options.setdefault('context', {})
        options['context'].update(**self.context)
        return serializer_cls(instance=instance, **options).data

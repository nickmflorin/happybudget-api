from factory.django import DjangoModelFactory
from factory.base import FactoryMetaClass


class FactoryRegistry:
    def __init__(self):
        self._registered = {}

    def add(self, model_cls, factory_cls):
        if model_cls in self._registered:
            raise Exception(
                f"Model {model_cls} is already registered with a factory!")
        self._registered[model_cls] = factory_cls

    def get(self, model_cls):
        if model_cls not in self._registered:
            raise Exception(
                f"Model {model_cls} does not have a registered factory.")
        return self._registered[model_cls]


registry = FactoryRegistry()


class ModelFactoryMetaClass(FactoryMetaClass):
    """
    Metaclass that will register all created model factory classes with the
    registry so the factory can be easily determined from a given model class
    at a later point in time.
    """
    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)
        if '_meta' in dct and hasattr(dct['_meta'], 'model') \
                and dct['_meta'].model is not None:
            registry.add(dct['_meta'].model, klass)
        return klass


class CustomModelFactory(DjangoModelFactory, metaclass=ModelFactoryMetaClass):
    @classmethod
    def create(cls, *args, **kwargs):
        created = super(CustomModelFactory, cls).create(*args, **kwargs)
        return cls.post_create(created, **kwargs)

    @classmethod
    def post_create(cls, model, **kwargs):
        return model

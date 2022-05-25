from django.db import models

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
    def post_create(cls, m, **kwargs):
        """
        Overrides the default `post_create()` method such that auto-now or
        auto-now-add fields can be explicitly set regardless of the time the
        model is saved.

        If a model has an auto-now or auto-now-add time related field, we cannot
        simply include this value in the factory kwargs since it will be
        overridden to the current time when the model is saved.  This method
        will force explicitly set values for an auto-now or auto-now-add
        time related field to be associated with the model by updating the
        model with those fields and then refreshing the model from the DB,
        which avoids saving the model directly and having those fields assume
        the current date/time as a value.
        """
        update_kwargs = {}
        for field in m.__class__._meta.get_fields():
            if isinstance(field, (models.DateField, models.DateTimeField)) \
                    and field.name in kwargs \
                    and (getattr(field, 'auto_now_add', None) is True
                    or getattr(field, 'auto_now', None) is True):
                update_kwargs[field.name] = kwargs[field.name]

        if update_kwargs:
            # Applying a direct update bypasses the auto time fields.
            m.__class__.objects.filter(pk=m.pk).update(**update_kwargs)
            m.refresh_from_db()
        return m

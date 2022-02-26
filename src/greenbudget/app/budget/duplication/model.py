import collections
import contextlib

from .exceptions import AssociatedObjectNotFound
from .utils import instantiate_duplicate


class ObjectRelationship:
    """
    An object representing the relationship between an original model class
    instance and it's duplicated form.
    """

    def __init__(self, instance, original, created=False, saved=False,
            update_fields=None):
        self.instance = instance
        self.original = original
        self.created = created
        self.saved = saved
        self.update_fields = update_fields or set([])

    @property
    def original_pk(self):
        return self.original.pk

    @property
    def new_pk(self):
        if self.instance.pk is None:
            raise Exception("Instance has not been saved yet!")
        return self.instance.pk


class ObjectSet(collections.abc.Mapping):
    """
    A mapping of the original instance ID to the :obj:`ObjectRelationship` for
    that original instance that is used to maintain the duplicated relationships
    for a given model class.
    """
    bulk_create_kwargs = {}

    def __init__(self, model_cls, user):
        self.user = user
        self.model_cls = model_cls
        # Data that stores a mapping of original model PKs to the associated
        # ObjectRelationship.
        self._data = {}

    @contextlib.contextmanager
    def transaction(self):
        try:
            yield self
        finally:
            self.clear()

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, pk):
        try:
            return self._data.__getitem__(pk)
        except KeyError:
            raise AssociatedObjectNotFound(self.model_cls, pk)

    def __setitem__(self, k, v):
        if k in self._data:
            raise KeyError(
                "Duplicated %s instance already exists for PK %s."
                % (self.model_cls.__name__, k)
            )
        self._data.__setitem__(k, v)

    def __len__(self):
        return self._data.__len__()

    def __delitem__(self, k):
        return self._data.__delitem__(k)

    def modify(self, pk, **kwargs):
        """
        Modifies the duplicated instance associated with the primary key
        value provided as `pk`.  The attributes provided as keyword arguments
        will be applied to the duplicated instance stored in the mapped data
        associated with the `pk` value.
        """
        instance = self[pk]
        for k, v in kwargs.items():
            setattr(instance.instance, k, v)
            # Denote the instance as requiring a save so that we know which
            # instances to include in the next bulk_update operation.
            instance.saved = False
            # Keep track of the fields updated for each instance so we can
            # include them in the bulk_update operation.
            instance.update_fields.add(k)

    def instantiate_duplicate(self, obj, **overrides):
        return instantiate_duplicate(
            instance=obj,
            user=self.user,
            destination_cls=self.model_cls,
            **overrides
        )

    @classmethod
    def from_join(cls, instances):
        """
        Creates a new :obj:`ObjectSet` instance by combining the data of several
        other :obj:`ObjectSet` instances, where the :obj:`ObjectSet` instances
        must be of the same form (same `user` and `model_cls` properties).
        """
        assert len(instances) != 0, "Must provide at least one instance to join."
        object_set = cls(
            model_cls=instances[0].model_cls,
            user=instances[0].user
        )
        for instance in instances:
            object_set.join(instance)
        return object_set

    def join(self, other):
        """
        Merges the data of the :obj:`ObjectSet` instance with another
        :obj:`ObjectSet` instance.
        """
        assert self.user == other.user and self.model_cls is other.model_cls, \
            "Cannot join two object sets that have different properties for " \
            "`model_cls` and `user`."
        for k, _ in other._data.items():
            if k in self._data:
                raise Exception(
                    "Cannot join two object sets that each have references to "
                    "the same key `%s`." % k
                )
            self._data[k] = other._data[k]

    def add(self, obj, **overrides):
        """
        Adds a new already-created instance to the set, creating it's associated
        duplicated version and associating them in a :obj:`ObjectRelationship`
        instance.
        """
        strict = overrides.pop('strict', True)
        if obj.pk not in self:
            self[obj.pk] = ObjectRelationship(
                instance=self.instantiate_duplicate(obj, **overrides),
                original=obj
            )
        elif strict:
            raise Exception('Relationship already exists for PK %s.' % obj.pk)

    def clear(self):
        # Isolate the instances that have been created but have not been saved
        # (due to changes since the last save or the first create) so they can
        # be bulk updated.
        not_saved = [
            (k, v) for k, v in self.items()
            if not v.saved and v.created
        ]
        # Isolate the instances that have not been created yet so they can be
        # bulk created in one batch.
        not_created = [
            (k, v) for k, v in self.items()
            if not v.created
        ]
        if not_created:
            instances = [ns[1].instance for ns in not_created]
            created = self.model_cls.objects.bulk_create(
                instances,
                **self.bulk_create_kwargs
            )
            assert len(created) == len(not_created), \
                "Suspicious query result: Bulk create tried to create %s " \
                "instances, but returned %s instances." \
                % (len(not_created), len(created))

            # Add the newly created instances back into the data,
            # attributing them as having been saved and created.
            for i, created_instance in enumerate(created):
                self._data[not_created[i][0]] = ObjectRelationship(
                    instance=created_instance,
                    created=True,
                    saved=True,
                    original=not_created[i][1].original,
                    update_fields=set([])
                )
        if not_saved:
            assert all([len(ns[1].update_fields) != 0 for ns in not_saved])

            update_fields = set([])
            for instance in [ns[1] for ns in not_saved]:
                update_fields.update(instance.update_fields)

            instances = [ns[1].instance for ns in not_saved]
            if instances:
                self.model_cls.objects.bulk_update(
                    instances, tuple(update_fields))

                # Update the instances post bulk_update to denote that they do
                # not need to be saved anymore and do not have any more changed
                # fields.
                for _, v in self.items():
                    v.saved = True
                    v.update_fields = []


class ConcreteObjectSet(ObjectSet):
    # The predetermination of PK values is only applicable for SQLite (tests).
    bulk_create_kwargs = {'predetermine_pks': True}


class PolymorphicObjectSet(ObjectSet):
    bulk_create_kwargs = {'return_created_objects': True}

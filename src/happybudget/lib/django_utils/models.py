import re

import collections
from polymorphic.models import PolymorphicModel

from model_utils import Choices as RootChoices

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

from happybudget.lib.utils import (
    humanize_list, ensure_iterable, ImmutableAttributeMapping)


class Choice:
    def __init__(self, name, slug):
        self.name = name
        self.slug = slug

    def __str__(self):
        return f"Choice name={self.name} slug={self.slug}"


class Choices(RootChoices):
    """
    Overrides the default :obj:`model_utils.Choices` implementation to provide
    the ability to access the slug model accessor of an individual choice.

    Typically, with the default :obj:`model_utils.Choices` key lookup on the
    object returns just the display name.

    class MyModel(models.Model):
        FRUITS = model_utils.Choices(
            (0, "apple", "Apple"),
            (1, "banana", "Banana"),
            (2, "strawberry", "Strawberry"),
        )
        fruit = models.IntegerField(choices=FRUITS)

    >>> MyModel.FRUITS[0]
    >>> "Apple"

    But for our purposes, we are interested in both the display name and the
    slug that is used to access the instance on the model.

    class MyModel(models.Model):
        FRUITS = happybudget.lib.django_utils.models.Choices(
            (0, "apple", "Apple"),
            (1, "banana", "Banana"),
            (2, "strawberry", "Strawberry"),
        )
        fruit = models.IntegerField(choices=FRUITS)

    >>> choice = MyModel.FRUITS[0]
    >>> <Choice name="Apple" slug="apple">
    >>> choice.slug
    >>> "apple"
    """
    @property
    def _slug_map(self):
        return {v: k for k, v in self._identifier_map.items()}

    @property
    def db_values(self):
        return self._db_values

    def __getitem__(self, key):
        assert isinstance(key, int), \
            "The provided choice must be the value that is stored in the " \
            "database, an integer."
        return Choice(name=self._display_map[key], slug=self._slug_map[key])

    def get_name(self, key):
        return self.__getitem__(key).name

    def get_slug(self, key):
        return self.__getitem__(key).slug

    def validate_values(self, *values):
        if len(values) == 1 and isinstance(values[0], (list, tuple)):
            values = values[0]
        else:
            values = list(values)
        invalid = [v for v in values if v not in self.db_values]
        if invalid:
            invalid = humanize_list(invalid)
            raise ValueError(
                f"Detected invalid value(s) {invalid} for choice class "
                f"{self.__class__}."
            )


def error_is_unique_constraint(err, field):
    """
    Returns whether or not a caught exception is an error related to a unique
    constraint validation failure for the provided field.

    This is a rather sensitive piece of logic, as changes to the error message
    of the IntegrityError can lead inaccurate results.  We should investigate
    a better way to do this.
    """
    if not isinstance(err, IntegrityError):
        return False
    regex = re.compile(
        "(?<=duplicatekeyvalueviolatesuniqueconstraint)"
        "(.*?)(?<=detail:key)(.*?)(?=alreadyexists.)"
    )
    result = re.search(regex, str(err).replace("\n", "").replace("\t", "")
        .replace(" ", "").lower())
    # The second group in the result (if it is not None) will be the tuple
    # of fields in the unique constraint and the violating values:
    # >>> '(content_type_id,object_id,"order")=(26,1621,n)'
    if result and field in result.group(2):
        return True
    return False


def get_model_polymorphic_ptr_field(model_cls, strict=False):
    """
    Returns the field used to point a child polymorphic model to its parent.
    """
    if len(model_cls._meta.parents) > 1:
        raise Exception("Multi-table inheritance not supported.")
    elif not model_cls._meta.parents:
        if strict:
            raise Exception(
                f"Model class {model_cls.__name__} does not exhibit "
                "multi-table inheritance and has no pointer field."
            )
        return None
    # Django does some weird things to prevent us from being able to access
    # the `parents` attribute on a model's Meta class as a normal dictionary.
    # The only thing we can do is iterate over it and treat them as tuples.
    data = model_cls._meta.parents.items()
    # Data will be an array of length-1 where the only element is a tuple.  That
    # tuple will have as it's first element the parent model class, and as it's
    # second element the field associating the parent model to the child model.
    if not issubclass(data[0][0], PolymorphicModel):
        if strict:
            raise Exception(
                f"Model class {model_cls.__name__} is not polymorphic.")
        return None
    return data[0][1].name


def import_model_at_path(*args):
    if len(args) == 1:
        path = args[0]
        if isinstance(path, tuple):
            return apps.get_model(app_label=path[0], model_name=path[1])
        return apps.get_model(
            app_label=path.split('.')[0],
            model_name=path.split('.')[1]
        )
    return apps.get_model(app_label=args[0], model_name=args[1],)


def generic_fk_instance_change(instance, obj_id_change=None,
        ct_change=None, obj_id_field='object_id', ct_field='content_type',
        assert_models=None):
    """
    With Generic Foreign Keys (GFKs) the object_id and the content_type are
    dependent on each other.  When combined, the object_id and content_type
    point to a specific :obj:`django.db.models.Model` instance.

    When we are tracking changes to these fields on a particular model, we need
    to carefully use the information provided to the signal to reconstruct what
    the previous GFK instance was and what the new GFK instance was.
    """
    if not hasattr(instance, 'previous_value'):
        raise Exception(
            "Instance %s is not tracked!" % instance.__class__.__name__)

    previous_obj_id = instance.previous_value(obj_id_field)
    new_obj_id = getattr(instance, obj_id_field)

    if obj_id_change is not None:
        previous_obj_id = obj_id_change.previous_value
        new_obj_id = obj_id_change.value

    new_ct = getattr(instance, ct_field)

    if ct_change is not None:
        # The previous value of a FK will be the ID, not the full object -
        # for reasons explained in happybudget.app.model.
        previous_ct = None
        if ct_change.previous_value is not None:
            previous_ct = ContentType.objects.get(pk=ct_change.previous_value)
        new_ct = ct_change.value
    else:
        previous_ct = instance.previous_value(ct_field)
        if previous_ct is not None:
            previous_ct = ContentType.objects.get(pk=previous_ct)

    new_instance = None
    if new_ct is not None:
        if assert_models is not None:
            assert new_ct.model_class() in assert_models
        new_instance = new_ct.model_class().objects.get(pk=new_obj_id)

    old_instance = None
    if previous_ct is not None:
        if assert_models is not None:
            assert previous_ct.model_class() in assert_models
        old_instance = previous_ct.model_class().objects.get(
            pk=previous_obj_id)

    return old_instance, new_instance


def _is_type_or_instance_of(k, v):
    return (isinstance(k, type) and (k is v or issubclass(k, v))) \
        or isinstance(k, v)


def model_types_to_array(k, recursing=False):
    if isinstance(k, str):
        return [import_model_at_path(k)]
    elif isinstance(k, type):
        return [k]
    # Recursion can only go one layer deep - i.e. we cannot have a tuple
    # where an element in the tuple is another tuple.
    elif isinstance(k, (tuple, list)) and not recursing:
        return [model_types_to_array(ki, recursing=True)[0] for ki in k]
    raise Exception(
        f"Invalid key of type {type(k)} provided in model map.  "
        "Must be type, a model path, or tuple of types/model paths."
    )


def get_value_from_model_map(model_map, instance, multiple=False, strict=True):
    values = [
        v for k, v in model_map.items()
        if any([
            _is_type_or_instance_of(instance, model_type)
            for model_type in model_types_to_array(k)
        ])
    ]
    if multiple:
        return values
    elif values:
        return values[0]
    elif strict:
        raise Exception(f"Could not map model type {type(instance)}.")
    return None


class ModelImportMap(ImmutableAttributeMapping):
    """
    A mapping class that maps keys to models (identified by the common string
    model definition for Django) such that accessing a key of the map will
    return the imported model.

    The common string model defintion for Django models is "<app_label>.<model>".
    """
    allow_caching = True

    def transform_value(self, v):
        return import_model_at_path(v)


class ModelMap(ImmutableAttributeMapping):
    """
    A mapping class that maps models (identified by the common string model
    definition for Django) to a set of values.  Lookups of the values can
    then be performed by accessing the map by an instance or a class type.

    The common string model defintion for Django models is "<app_label>.<model>".
    """

    def get(self, model_type_or_instance, multiple=False, strict=True):
        return get_value_from_model_map(
            self._store,
            model_type_or_instance,
            multiple=multiple,
            strict=strict
        )


def find_model_types_in_set(instance, types, strict=True, multiple=False):
    tps = [t for t in model_types_to_array(types) if isinstance(instance, t)]
    if len(tps) == 0:
        if strict:
            raise Exception(
                f"Instance type {type(instance)} is not included in provided "
                f"set, {humanize_list(types)}."
            )
        return None
    elif len(tps) > 1:
        if not multiple:
            raise Exception(
                f"Instance type {type(instance)} is a sub type of multiple "
                f"provided types in {humanize_list(types)}."
            )
        return tps
    return tps


def group_models_by_type(instances, types=None, multiple=False, strict=True):
    types = types or set([type(i) for i in instances])
    grouped = collections.defaultdict(list)
    for instance in ensure_iterable(instances):
        if types is not None:
            instance_types = find_model_types_in_set(
                instance, types, strict=strict, multiple=multiple)
            for i_type in ensure_iterable(instance_types):
                grouped[i_type].append(instance)
        else:
            grouped[type(instance)].append(instance)
    return grouped

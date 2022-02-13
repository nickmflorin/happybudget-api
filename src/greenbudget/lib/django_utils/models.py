import collections

from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from greenbudget.lib.utils import humanize_list, ensure_iterable


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
        # for reasons explained in greenbudget.app.model.
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


class ModelMap(collections.abc.Mapping):
    def __init__(self, store):
        self._store = store

    def get(self, model_type_or_instance, multiple=False, strict=True):
        return get_value_from_model_map(
            self._store,
            model_type_or_instance,
            multiple=multiple,
            strict=strict
        )

    def __getitem__(self, k):
        return self._store[k]

    def __iter__(self):
        return self._store.__iter__()

    def __len__(self):
        return self._store.__len__()

    def __repr__(self):
        return self._store.__repr__()


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

import datetime

from .config import DT_FIELDS, ALLOW_FIELD_OVERRIDES, DISALLOWED_FIELDS
from .fields import AllowedFieldOverride


def field_obj_is_allowed_by_override(field, model_cls, value, user):
    override = ALLOW_FIELD_OVERRIDES.get(model_cls, strict=False)
    if override is None:
        return False
    if isinstance(override, AllowedFieldOverride):
        return override.is_overridden(field, value, user)
    assert hasattr(override, '__iter__')
    return any([o.is_overridden(field, value, user) for o in override])


def field_obj_is_disallowed(field, model_cls, value, user):
    disallowed = any([obj.is_disallowed(field) for obj in DISALLOWED_FIELDS])
    if disallowed and field_obj_is_allowed_by_override(
            field, model_cls, value, user):
        return False
    return disallowed


def field_can_be_duplicated(field, model_cls, value, user):
    return not field_obj_is_disallowed(field, model_cls, value, user)


def instantiate_duplicate(instance, user, **overrides):
    kwargs = {}
    destination_cls = overrides.pop('destination_cls', type(instance))
    for field_obj in type(instance)._meta.fields:
        if field_obj in destination_cls._meta.fields \
                and field_obj.name not in overrides:
            instance_value = getattr(instance, field_obj.name)
            can_be_duplicated = field_can_be_duplicated(
                field=field_obj,
                model_cls=type(instance),
                value=instance_value,
                user=user
            )
            if can_be_duplicated:
                kwargs[field_obj.name] = getattr(instance, field_obj.name)
            elif isinstance(field_obj, DT_FIELDS) \
                    and (field_obj.auto_now_add or field_obj.auto_now):
                kwargs[field_obj.name] = datetime.datetime.now()

    if hasattr(instance.__class__, 'created_by'):
        kwargs['created_by'] = user
    if hasattr(instance.__class__, 'updated_by'):
        kwargs['updated_by'] = user
    return destination_cls(**kwargs, **overrides)

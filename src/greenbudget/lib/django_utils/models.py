from polymorphic.models import PolymorphicModel
from django.contrib.contenttypes.models import ContentType
from django.db import models


def bulk_create_polymorphic_model(instances):
    assert len(set([type(inst) for inst in instances])) == 1, \
        "Not all instances are of the same type."

    model_cls = type(instances[0])
    assert len(model_cls.__bases__) == 0, "Multi-inheritance not supported."
    assert hasattr(model_cls, 'non_polymorphic') \
        and isinstance(
            getattr(model_cls, 'non_polymorphic', models.Manager)), \
        "%s must define a `non_polymorphic` manager." % model_cls.__name__

    polymorphic_base = model_cls.__bases__[0]
    assert issubclass(polymorphic_base, PolymorphicModel), \
        "%s is not a Polymorphic model!" % model_cls.__name__

    def get_base_model_kwargs(instance):
        kwargs = {}
        for field in polymorphic_base._meta.fields:
            if not isinstance(field, models.fields.AutoField) \
                    and field.name != "polymorphic_ctype":
                kwargs[field] = getattr(instance, field)
        kwargs['polymorphic_ctype'] = ContentType.objects.get_for_model(
            model_cls)
        return kwargs

    def get_child_model_kwargs(instance):
        kwargs = {}
        for field in model_cls._meta.fields:
            if not isinstance(field, models.fields.AutoField) \
                    and field.name != "polymorphic_ctype" \
                    and field not in polymorphic_base._meta.fields:
                kwargs[field] = getattr(instance, field)
        return kwargs

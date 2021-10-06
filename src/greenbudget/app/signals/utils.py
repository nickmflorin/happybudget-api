from django.contrib.contenttypes.models import ContentType


def generic_foreign_key_instance_change(instance, obj_id_change=None,
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
    if obj_id_change is None and ct_change is None:
        raise ValueError(
            "Either the change corresponding to the content_type or the "
            "object_id must be provided."
        )

    previous_obj_id = getattr(instance, obj_id_field)
    new_obj_id = getattr(instance, obj_id_field)

    if obj_id_change is not None:
        previous_obj_id = obj_id_change.previous_value
        new_obj_id = obj_id_change.value

    previous_ct = getattr(instance, ct_field)
    new_ct = getattr(instance, ct_field)

    if ct_change is not None:
        # The previous value of a FK will be the ID, not the full object -
        # for reasons explained in greenbudget.signals.models.
        previous_ct = None
        if ct_change.previous_value is not None:
            previous_ct = ContentType.objects.get(pk=ct_change.previous_value)
        new_ct = ct_change.value

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

    assert new_instance != old_instance
    return old_instance, new_instance

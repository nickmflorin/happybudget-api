from polymorphic.models import PolymorphicModel
from django.db import models


def BaseModel(polymorphic=False, **kwargs):
    """
    Model factory that creates an abstract base model, optionally polymorphic,
    that should should be used for all pertinent models in the application.

    The factory-created base model class incorporates create and update tracking
    of model instances.
    """
    base_cls = PolymorphicModel if polymorphic else models.Model

    activity_fields = [
        'updated_at', 'created_at', 'updated_by', 'created_by']
    active_activity_fields = []

    kwargs.setdefault('updated_at', models.DateTimeField(auto_now=True))
    kwargs.setdefault('created_at', models.DateTimeField(auto_now_add=True))
    # By default, if the User who updated the instance is removed - the
    # instances will simply denote the updated by User as None.
    kwargs.setdefault('updated_by', models.ForeignKey(
        to='user.User',
        related_name=kwargs.pop(
            'updated_by_related_name',
            'updated_%(class)ss'
        ),
        on_delete=kwargs.pop('updated_by_on_delete', models.SET_NULL),
        editable=False,
        null=True
    ))
    # By default, if the User who created the instance is removed - the
    # instances they created will also be removed.
    kwargs.setdefault('created_by', models.ForeignKey(
        to='user.User',
        related_name=kwargs.pop(
            'created_by_related_name',
            'created_%(class)ss'
        ),
        on_delete=kwargs.pop('created_by_on_delete', models.CASCADE),
        editable=False
    ))

    def get_field(field):
        if kwargs[field] is None:
            # The field will be removed from the model attributes so we simply
            # return None.
            return None
        assert isinstance(kwargs[field], models.Field), \
            f"Invalid field {type(kwargs[field])} provided, expected " \
            f"of type {type(models.Field)}."
        active_activity_fields.append(field)
        return kwargs[field]

    class _BaseModel(base_cls):
        created_at = get_field('created_at')
        created_by = get_field('created_by')
        updated_at = get_field('updated_at')
        updated_by = get_field('updated_by')

        class Meta:
            abstract = True

    # Dynamically setting the fields on the model cls based on whether or not
    # they are excluded from the **kwargs messes with Django's internal
    # mechanics, so the only way that we can ensure that the model class does
    # not have the attribute (versus having a value of None for the attribute)
    # is to delete them from the model class after the fact.
    for k in activity_fields:
        if k not in active_activity_fields:
            delattr(_BaseModel, k)

    def mark_updated(instance, *args, **kwargs):
        """
        Marks the instance as having been updated when the model class is
        attributed with the `updated_at` and/or `updated_by` fields.  In the
        case that the instance is attributed with the `updated_by` field, the
        :obj:`User` is a required argument to the method.

        This method is only pertinent when the update is performed inside of
        the request context with an actively logged in :obj:`User`.
        """
        # pylint: disable=import-outside-toplevel
        from happybudget.app.user.models import User

        # This should be prevented based on the manner in which this method is
        # attached to the class.
        assert hasattr(instance, 'updated_by') or hasattr(instance, 'updated_at')

        def pluck_user():
            assert args or 'user' in kwargs, \
                "Model class {instance.__class__} defines a `updated_by` " \
                "field, so the user is a required argument."
            if args:
                if len(args) != 1 or kwargs:
                    raise TypeError("Improper usage of method.")
                return args[0]
            return kwargs['user']

        update_fields = []

        if hasattr(instance, 'updated_at'):
            update_fields.append('updated_at')

        if hasattr(instance, 'updated_by'):
            user = pluck_user()
            if not isinstance(user, User):
                raise ValueError(f"Expected type {User}, not {type(user)}.")
            elif not user.is_fully_authenticated:
                raise Exception(
                    f"Unauthenticated user {user.pk} trying to update instance.")
            update_fields.append('updated_by')
            setattr(instance, 'updated_by', user)

        instance.save(update_fields=update_fields)

    if hasattr(_BaseModel, 'updated_at') or hasattr(_BaseModel, 'updated_by'):
        setattr(_BaseModel, 'mark_updated', mark_updated)
    return _BaseModel

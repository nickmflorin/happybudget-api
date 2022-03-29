import functools

from django.db import models

from greenbudget.lib.utils import empty, ensure_iterable

from .bulk_actions import *  # noqa
from .bulk_registration import *  # noqa


def children_method_handler(func):
    """
    Decorates a methods on a :obj:`BaseBudget`, :obj:`Account` or
    :obj:`SubAccount` that accept a `children` argument and perform calculations
    based on the accumulation of values of the children of the instance whose
    method this decorates.

    Exposed Parameters:
    ------------------
    The decorator will expose the following parameters on the method:

    children: :obj:`django.db.models.QuerySet` or an iterable (optional)
        The children that should be used to perform the calculation.  If
        omitted, the `children` will be determined from a database query
        of the related models on the instance that are defined to be the
        children.

        Default: None

    children_to_delete: :obj:`list`, :obj:`tuple` or another iterable (optional)
        A iterable of IDs associated with the children of the instance that are
        going to be deleted.  If provided, the children associated with these
        IDs will be excluded from the calculation.

        Default: None

    unsaved_children: :obj:`list` or :obj:`tuple` or another iterable
        An iterable of children instances that have been updated but not yet
        persisted to the database.  If provided, the children that are either
        explicitly provided or determined from a database query will be
        supplemented with the updated forms of the instances dictated by this
        parameter.

        This is important when performing bulk changes, as there are cases where
        we want to reperform calculations on models but have not yet saved
        children of the model instance that were updated to the database yet.

        Note:  Unsaved does not mean never-saved, the unsaved children should
               all have associated IDs.

        Default: None

    All of the exposed parameters are combined to a single `children` parameter
    that the method is then called with.
    """
    @functools.wraps(func)
    def inner(instance, *args, **kwargs):
        # Any potential children that are going to be deleted but have yet to
        # be deleted from the database.  These children will be exclued from
        # the children passed into the method.
        children_to_delete = kwargs.pop('children_to_delete', []) or []

        # Any potential children to the instance that have been altered but not
        # yet persisted to the database.  These instances will supplement the
        # children passed into the method such that the children passed into the
        # method contain up to date information - even if it hasn't persisted
        # to the database yet.
        unsaved_children = kwargs.pop('unsaved_children', []) or []

        # We have to be careful with empty lists here, because an empty list
        # means there are no children - so we cannot simply check `if children`.
        children = kwargs.pop('children', empty)
        if children is empty:
            if args:
                children = args[0]
            else:
                # Perform the database query to get the instance children.
                # Note that these children will not be representative of any
                # unsaved changes until they are supplemented with the
                # `unsaved_children`.
                children = instance.children.all()

        assert all([
            pk in [c.pk for c in children] for pk in children_to_delete]), \
            "The children to delete must be provided as IDs of children that " \
            "exist in the instance's children or provided children."

        # If the estimation is being performed in the context of children
        # that are not yet saved (due to bulk write behavior) then we need to
        # make sure to reference the value from that unsaved child, not the
        # child that is pulled from the database.
        if isinstance(children, models.QuerySet):
            children = list(children.exclude(
                # Unsaved does not mean never saved, the child could have a PK.
                pk__in=[c.pk for c in unsaved_children if c.pk is not None]
            ))
        else:
            children = [c for c in children if c.pk not in [
                c.pk for c in unsaved_children if c.pk is not None]]
        children += ensure_iterable(unsaved_children)
        return func(
            instance,
            [c for c in children if c.pk not in children_to_delete],
            **kwargs
        )
    return inner

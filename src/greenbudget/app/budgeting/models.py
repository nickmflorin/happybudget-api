import functools

from greenbudget.lib.utils.decorators import optional_parameter_decorator


@optional_parameter_decorator
def use_children(func, fields=None):
    @functools.wraps(func)
    def inner(instance, *args, **kwargs):
        if not hasattr(instance, 'children'):
            raise Exception(
                "Decorator can only be used for models with defined "
                "children."
            )
        if 'children' not in kwargs:
            children_to_be_deleted = kwargs.pop('children_to_be_deleted', [])
            kwargs['children'] = instance.children.exclude(
                pk__in=children_to_be_deleted or []
            )
            if fields is not None:
                kwargs['children'] = kwargs['children'].only(*fields)
        return func(instance, *args, **kwargs)
    return inner


@optional_parameter_decorator
def use_actuals(func, fields=None):
    @functools.wraps(func)
    def inner(instance, *args, **kwargs):
        if not hasattr(instance, 'actuals'):
            raise Exception(
                "Decorator can only be used for models with defined "
                "actuals."
            )
        if 'actuals' not in kwargs:
            actuals_to_be_deleted = kwargs.pop('actuals_to_be_deleted', [])
            kwargs['actuals'] = instance.actuals.exclude(
                pk__in=actuals_to_be_deleted or []
            )
            if fields is not None:
                kwargs['actuals'] = kwargs['actuals'].only(*fields)
        return func(instance, *args, **kwargs)
    return inner


@optional_parameter_decorator
def use_markup_children(func, fields=None):
    @functools.wraps(func)
    def inner(instance, *args, **kwargs):
        if not hasattr(instance, 'children_markups'):
            raise Exception(
                "Decorator can only be used for models with defined "
                "children_markups."
            )
        if 'children_markups' not in kwargs:
            markups_to_be_deleted = kwargs.pop('markups_to_be_deleted', [])
            kwargs['children_markups'] = instance.children_markups.exclude(
                pk__in=markups_to_be_deleted or []
            )
            if fields is not None:
                kwargs['children_markups'] = kwargs['children_markups'].only(*fields)  # noqa
        return func(instance, *args, **kwargs)
    return inner


@optional_parameter_decorator
def use_markups(func, fields=None):
    @functools.wraps(func)
    def inner(instance, *args, **kwargs):
        if not hasattr(instance, 'markups'):
            raise Exception(
                "Decorator can only be used for models with defined "
                "markups."
            )
        if 'markups' not in kwargs:
            markups_to_be_deleted = kwargs.pop('markups_to_be_deleted', [])
            kwargs['markups'] = instance.markups.exclude(
                pk__in=markups_to_be_deleted or []
            )
            if fields is not None:
                kwargs['markups'] = kwargs['markups'].only(*fields)
        return func(instance, *args, **kwargs)
    return inner

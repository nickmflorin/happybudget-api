import functools

from greenbudget.lib.utils.decorators import optional_parameter_decorator


@optional_parameter_decorator
def use_fringes(func, fields=None):
    @functools.wraps(func)
    def inner(instance, *args, **kwargs):
        if not hasattr(instance, 'fringes'):
            raise Exception(
                "Decorator can only be used for models with defined "
                "fringes."
            )
        if 'fringes' not in kwargs:
            fringes_to_be_deleted = kwargs.pop('fringes_to_be_deleted', [])
            kwargs['fringes'] = instance.fringes.exclude(
                pk__in=fringes_to_be_deleted or []
            )
            if fields is not None:
                kwargs['fringes'] = kwargs['fringes'].only(*fields)
        return func(instance, *args, **kwargs)
    return inner

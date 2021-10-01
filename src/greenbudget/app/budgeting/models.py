import functools


def use_children(fields):
    def decorator(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            kwargs['children'] = kwargs.get('children')
            if kwargs['children'] is None:
                kwargs['children'] = instance.children.exclude(
                    pk__in=kwargs.get('children_to_be_deleted', []) or []
                ).only(*fields).all()
            func(instance, *args, **kwargs)
        return inner
    return decorator

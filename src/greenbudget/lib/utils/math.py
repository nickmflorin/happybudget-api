from .builtins import ensure_iterable, concat, humanize_list


def cumulative_operation(operation, *values, **kwargs):
    array = list(values)
    if len(values) == 1:
        array = values[0]
        assert hasattr(array, '__iter__'), \
            "The provided value is not an iterable."

    attr = kwargs.pop('attr', None)
    if attr is not None:
        attr = ensure_iterable(attr)
        assert all([isinstance(ai, str) for ai in attr]), \
            "Encountered not string attribute values."

        if any([not all([hasattr(vi, a) for a in attr]) for vi in array]):
            raise Exception(
                f"Encountered values without attributes {humanize_list(attr)}.")
        # If multiple attributes are provided, each will be counted toward
        # the cumulative amount.
        array = concat([[getattr(vi, ai) for ai in attr] for vi in array])

    ignore_values = kwargs.pop('ignore_values', [])
    if ignore_values is None:
        ignore_values = [None]
    else:
        ignore_values = ensure_iterable(ignore_values)
    array = [vi for vi in array if vi not in ignore_values]

    assert not ('initial_value' not in kwargs and len(array) == 0), \
        "If no initial value is specified, at least one valid value must be " \
        "provided."

    if any([
        not isinstance(vi, int) and not isinstance(vi, float)
        for vi in array
    ]):
        raise Exception("Encountered non-numeric values.")

    if len(array) == 0:
        return kwargs['initial_value']

    cumulative = array[0]
    for v in array[1:]:
        cumulative = operation(cumulative, v)
    return cumulative


def cumulative_product(*values, **kwargs):
    return cumulative_operation(lambda a, b: a * b, *values, **kwargs)


def cumulative_sum(*values, **kwargs):
    kwargs.setdefault('initial_value', 0.0)
    return cumulative_operation(lambda a, b: a + b, *values, **kwargs)

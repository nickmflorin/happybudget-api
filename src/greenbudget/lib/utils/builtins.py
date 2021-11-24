import importlib
import six


def set_or_list(obj):
    if isinstance(obj, set):
        return list(obj)
    elif not hasattr(obj, '__iter__'):
        return [obj]
    return list(obj)


def get_nested_attribute(obj, attr):
    if '.' in attr:
        parts = attr.split('.')
        if not hasattr(obj, parts[0]):
            raise AttributeError('Object does not have attribute %s.' % parts[0])
        return get_nested_attribute(getattr(obj, parts[0]), '.'.join(parts[1:]))
    return getattr(obj, attr)


def humanize_list(value, callback=six.text_type, conjunction='and',
        oxford_comma=True):
    """
    Turns an interable list into a human readable string.
    """
    num = len(value)
    if num == 0:
        return ""
    elif num == 1:
        return callback(value[0])
    s = u", ".join(map(callback, value[:num - 1]))
    if len(value) >= 3 and oxford_comma is True:
        s += ","
    return "%s %s %s" % (s, conjunction, callback(value[num - 1]))


def conditionally_separate_strings(strings, separator=" "):
    parts = [pt for pt in strings if pt is not None]
    assert all([isinstance(pt, str) for pt in parts])
    if len(parts) == 0:
        return ""
    elif len(parts) == 1:
        return parts[0]
    return separator.join(parts)


def import_at_module_path(module_path):
    module_name = ".".join(module_path.split(".")[:-1])
    class_name = module_path.split(".")[-1]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def concat(arrays):
    """
    Concatenates an array of arrays into a 1 dimensional array.
    """
    if not isinstance(arrays, list):
        raise ValueError("Can only concatenate objects of list type.")
    elif len(arrays) == 0:
        return []
    concatenated = arrays[0]
    if not isinstance(concatenated, list):
        raise ValueError(
            "Each element in the concatenation must be an instance "
            "of `list`."
        )
    if len(arrays) > 1:
        for array in arrays[1:]:
            if not isinstance(array, list):
                raise ValueError(
                    "Each element in the concatenation must be an instance "
                    "of `list`."
                )
            concatenated += array
    return concatenated


def ensure_iterable(value, strict=False, cast=list):
    """
    Ensures that the provided value is an iterable, either raising a ValueError
    (if `strict = True`) or returning the value as the first element in an
    iterable (if `strict = False`).
    """
    if value is None:
        return cast()
    if isinstance(value, str):
        return [value]
    if not hasattr(value, '__iter__') or isinstance(value, type):
        if strict:
            raise ValueError("Value %s is not an iterable." % value)
        return cast([value])
    return value

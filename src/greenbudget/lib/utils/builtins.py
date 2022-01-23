import importlib
import six


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.
    It is required because `None` may be a valid input or output value.
    """
    pass


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


def get_nested_attribute(obj, attr):
    if '.' in attr:
        parts = attr.split('.')
        if not hasattr(obj, parts[0]):
            raise AttributeError('Object does not have attribute %s.' % parts[0])
        return get_nested_attribute(getattr(obj, parts[0]), '.'.join(parts[1:]))
    return getattr(obj, attr)


def get_string_formatted_kwargs(value):
    """
    Returns the string arguments that are used to format the string.  For
    example, in the string `Foo {bar}`, the string would be formatted as
    .format(bar='foo').  In this case, this method will return ["bar"],
    indicating that `bar` is the only argument needed to format the string.
    """
    formatted_kwargs = []
    current_formatted_kwarg = None
    for char in value:
        if char == "{":
            current_formatted_kwarg = ""
        elif char == "}":
            if current_formatted_kwarg is not None:
                formatted_kwargs.append(current_formatted_kwarg)
                current_formatted_kwarg = None
        else:
            if current_formatted_kwarg is not None:
                current_formatted_kwarg = current_formatted_kwarg + char
    return formatted_kwargs


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
    Ensures that the provided value is an iterable that can be indexed
    numerically.
    """
    if value is None:
        return cast()
    # A str instance has an `__iter__` method.
    if isinstance(value, str):
        return [value]
    elif hasattr(value, '__iter__') and not isinstance(value, type):
        # We have to cast the value instead of just returning it because a
        # instance of set() has the `__iter__` method but is not indexable.
        return cast(value)
    elif strict:
        raise ValueError("Value %s is not an iterable." % value)
    return cast([value])

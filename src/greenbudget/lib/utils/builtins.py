import importlib
import inspect


def conditionally_separate_strings(strings, separator=" "):
    parts = [pt for pt in strings if pt is not None]
    assert all([isinstance(pt, str) for pt in parts])
    if len(parts) == 0:
        return ""
    elif len(parts) == 1:
        return parts[0]
    return separator.join(parts)


def get_function_keyword_defaults(func):
    arg_spec = inspect.getfullargspec(func)
    positional_count = len(arg_spec.args)
    defaults = {}
    if arg_spec.defaults is not None:
        positional_count = positional_count - len(arg_spec.defaults)

        defaults = dict(zip(
            arg_spec.args[positional_count:],
            arg_spec.defaults
        ))
    return defaults


def import_at_module_path(module_path):
    module_name = ".".join(module_path.split(".")[:-1])
    class_name = module_path.split(".")[-1]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def is_non_string_iterable(value):
    return hasattr(value, '__iter__') and not isinstance(value, str)


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

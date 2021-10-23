import hashlib
import importlib
import inspect
import json
import re
from typing import Dict, Any

from .dateutils import ensure_datetime


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


def hash_dict(dictionary: Dict[str, Any]) -> str:
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


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


def is_datetime(value):
    """
    Returns whether or not the value is a valid :obj:`datetime.datetime`
    instance, a valid :obj:`datetime.date` instance, or a string that can be
    converted to either.
    """
    try:
        ensure_datetime(value)
    except ValueError:
        return False
    else:
        return True


def find_in_dict(data, keys):
    """
    Finds the value in a potentially nested dictionary by a key or set of
    nested keys.

    Parameters:
    ----------
    data: :obj:`dict`
        The dictionary for which we want to find the value indexed by the
        potentially nested keys.
    keys: :obj:`list`, :obj:`tuple`, :obj:`str`
        Either an iterable of nested keys or a single key for which we want
        to locate the associated value in the dictionary for.

    Example:
    -------
    >>> data = {'foo': {'bar': 'banana'}}
    >>> find_in_dict(data, 'foo')
    >>> {'bar': 'banana'}
    >>> find_in_dict(data, ['foo', 'bar'])
    >>> 'banana'
    """
    if hasattr(keys, '__iter__') and not isinstance(keys, str):
        if len(keys) == 1:
            return data[keys[0]]
        current = data[keys[0]]
        for key in keys[1:]:
            current = current[key]
        return current
    return data[keys]


def place_in_dict(data, keys, value):
    """
    Places a value in a potentially nested dictionary at the location defined
    by a set potentially nested keys.

    Parameters:
    ----------
    data: :obj:`dict`
        The dictionary for which the value will be stored in.
    keys: :obj:`list`, :obj:`tuple`, :obj:`str`
        Either an iterable of nested keys or a single key that defines the
        location in the dictionary for which the value should be stored.
    value:
        The value to store in the dictionary.

    Example:
    -------
    >>> data = {'foo': {'bar': 'banana'}}
    >>> place_in_dict(data, 'foo', 'bar')
    >>> data
    >>> {'foo': 'bar'}
    >>> place_in_dict(data, ['foo', 'bar'], 'bar')
    >>> data
    >>> {'foo': {'bar': 'bar'}}
    """
    if hasattr(keys, '__iter__') and not isinstance(keys, str):
        if len(keys) == 1:
            data[keys[0]] = value
            return
        current = data[keys[0]]
        for key in keys[1:-1]:
            current = current[key]
        current[keys[-1]] = value
    else:
        data[keys] = value


def find_string_formatted_arguments(value):
    """
    Finds arguments in a string that are meant to be string formatted.

    Example:
    -------
    >>> value = "{argument1}, the fox jumped over the {argument2}"
    >>> find_string_formatted_arguments(value)
    >>> ["argument1", "argument2"]
    """
    regex = '[^{\}]+(?=})'  # noqa
    matches = re.findall(regex, value)
    if matches is None:
        return []

    arguments = []
    index = 0
    while True:
        try:
            arguments.append(matches[index])
        except IndexError:
            break
        else:
            index += 1
    return arguments


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

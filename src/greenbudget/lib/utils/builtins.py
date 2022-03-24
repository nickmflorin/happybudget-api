import copy
import importlib
import six


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.
    It is required because `None` may be a valid input or output value.
    """


class DynamicArgumentException(Exception):
    """
    An abstract exception class that will dynamically inject provided arguments
    into the exception message if they are present as string formatted arguments.

    Extensions of the :obj:`DynamicArgumentException` class can be configured
    with default messages such that messages are only used on initialization
    if they are provided.

    Usage:
    -----
    >>> class MyException(DynamicArgumentException):
    >>>     default_message = "The fox jumped over the {obj}."
    >>>
    >>> exc = MyException(obj='log')
    >>> str(exc)
    >>> "The fox jumped over the log."
    >>>
    >>> exc = MyException("The dog is in a {mood} mood.", mood='happy')
    >>> str(exc)
    >>> "The dog is in a happy mood."
    """

    def __init__(self, *args, **kwargs):
        assert len(args) == 1 or 'message' in kwargs \
            or hasattr(self, 'default_message'), \
            f"Improper usage of {self.__class__.__name__}.  The message must " \
            "be defined statically on the class or provided on initialization."

        self._message = getattr(self, 'default_message', None)
        if 'message' in kwargs or len(args) != 0:
            self._message = kwargs.pop('message', None)
            if len(args) == 1:
                self._message = args[0]

        self._kwargs = kwargs

    @property
    def message(self):
        format_kwargs = copy.deepcopy(self._kwargs)
        formatters = getattr(self, 'formatters', {})
        assert isinstance(formatters, dict), \
            f"The formatters on the {self.__class__.__name__} class must be " \
            f"of type {type(dict)}."

        for k, v in format_kwargs.items():
            if k in formatters:
                assert hasattr(formatters[k], '__call__'), \
                    "Each formatter must be a callable."
                format_kwargs[k] = formatters[k](v)
        return conditionally_format_string(self._message, **format_kwargs)

    def __str__(self):
        return self.message


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
    if conjunction:
        s = u", ".join(map(callback, value[:num - 1]))
        if len(value) >= 3 and oxford_comma is True:
            s += ","
        return "%s %s %s" % (s, conjunction, callback(value[num - 1]))
    return u", ".join(map(callback, value[:num]))


def get_nested_attribute(obj, attr):
    if '.' in attr:
        parts = attr.split('.')
        if not hasattr(obj, parts[0]):
            raise AttributeError('Object does not have attribute %s.' % parts[0])
        return get_nested_attribute(getattr(obj, parts[0]), '.'.join(parts[1:]))
    return getattr(obj, attr)


def get_attribute(*args, **kwargs):
    """
    Retrieves an attribute from either the provided instance, provided
    :obj:`dict` or from the set of provided keyword arguments.
    """
    strict = kwargs.pop('strict', True)
    default = kwargs.pop('default', None)

    def get_from_dict(v, k):
        if strict:
            return v[k]
        return v.get(k, default)

    def get_from_instance(v, k):
        if strict:
            return getattr(v, k)
        return getattr(v, k, default)

    assert len(args) == 2 or (kwargs and len(args) == 1), \
        "The attribute must be obtained from either a provided dict, " \
        "instance or set of keyword arguments, and none of these were " \
        "provided."

    if len(args) == 2:
        if isinstance(args[1], dict):
            return get_from_dict(args[1], args[0])
        return get_from_instance(args[1], args[0])
    return get_from_dict(kwargs, args[0])


def get_string_formatted_kwargs(value):
    """
    Returns the string arguments that are used to format the string.

    Example:
    --------
    In the string foo = "Hello {world}", the string foo would be formatted as
    foo.format(world='bar').  In this case, this method will return ["world"],
    indicating that `world` is the only argument needed to format the string.
    """
    formatted_kwargs = []
    current_formatted_kwarg = None
    for char in value:
        if char == "{":
            current_formatted_kwarg = ""
        elif char == "}":
            if current_formatted_kwarg is not None:
                if current_formatted_kwarg not in formatted_kwargs:
                    formatted_kwargs.append(current_formatted_kwarg)
                current_formatted_kwarg = None
        else:
            if current_formatted_kwarg is not None:
                current_formatted_kwarg = current_formatted_kwarg + char
    return formatted_kwargs


def conditionally_format_string(string, **kwargs):
    """
    Traditionally, when you have a string with format arguments in it, calling
    .format() on the string and not providing all of the arguments will raise
    an exception.

    Here, we loosen that constraint and will only format the string with the
    provided arguments if they are in the string, and any formatted arguments
    in the string that are not provided will be left as is.
    """
    string_formatted_args = get_string_formatted_kwargs(string)
    for string_f_arg in [
        a for a in string_formatted_args
        if a in kwargs and kwargs[a] is not None
    ]:
        string = string.replace("{%s}" % string_f_arg, kwargs[string_f_arg])
    return string


def conditionally_separate_strings(strings, separator=" "):
    """
    Returns a string that is generated from joining the provided strings with
    the provided separator, filtering out values of None from the provided
    strings.

    Usage:
    -----
    >>> conditionally_separate_strings(["foo", "bar", None])
    >>> "foo bar"
    """
    parts = [pt for pt in strings if pt is not None]
    assert all([isinstance(pt, str) for pt in parts])
    if len(parts) == 0:
        return ""
    elif len(parts) == 1:
        return parts[0]
    return separator.join(parts)


def import_at_module_path(module_path):
    """
    Imports the class or function at the provided module path.
    """
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


def ensure_iterable(value, strict=False, cast=list, cast_none=True):
    """
    Ensures that the provided value is an iterable that can be indexed
    numerically.
    """
    if value is None:
        if cast_none:
            return cast()
        return None
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

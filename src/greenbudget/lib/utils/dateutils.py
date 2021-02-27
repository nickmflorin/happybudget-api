import datetime
from dateutil import parser

from django.conf import settings
from rest_framework.settings import api_settings

from greenbudget.conf import Environments


def api_datetime_string(value):
    """
    Parses either a provivded `obj:datetime.datetime` instance, a provided
    `obj:datetime.date` instance or a valid date formatted `obj:str` instance
    into a date formatted string that is consistent with the way our
    API renders datetimes in responses.

    The default time format for API responses is iso-8601.

    Args:
        value (`obj:datetime.datetime`, `obj:datetime.date` or `obj:str)
            The value that should be converted to a datetime string.
    """
    value = ensure_datetime(value)
    return value.strftime(api_settings.DATETIME_FORMAT)


def ensure_datetime(value):
    """
    Ensures that the provided value is a `obj:datetime.datetime` instance
    by either converting a `obj:str` to a `obj:datetime.datetime` instance
    or a `obj:datetime.date` instance to a `obj:datetime.datetime` instance.

    If the value cannot be safely converted to a `obj:datetime.datetime`
    instance, a ValueError will be raised.

    Args:
        value (`obj:datetime.datetime`, `obj:datetime.date` or `obj:str)
            The value that should be converted to a `obj:datetime.datetime`
            instance.
    """
    if type(value) is datetime.datetime:
        return value
    elif type(value) is datetime.date:
        return datetime.datetime.combine(value, datetime.datetime.min.time())
    elif isinstance(value, str):
        try:
            return parser.parse(value)
        except ValueError:
            raise ValueError(
                "The provided value cannot be converted to a "
                "datetime.datetime instance."
            )
    else:
        # A work around to allow our tests to use this logic in the presence
        # of pytest-freezegun.  pytest-freezegun works by replacing the datetime
        # module with it's own implementation.
        if (settings.ENVIRONMENT == Environments.TEST
                and datetime.datetime.__class__.__name__ == "FakeDatetimeMeta"):
            return value
        raise ValueError(
            "Invalid value %s supplied - cannot convert to datetime." % value)


def ensure_date(value):
    """
    Ensures that the provided value is a `obj:datetime.date` instance
    by either converting a `obj:str` to a `obj:datetime.date` instance
    or a `obj:datetime.datetime` instance to a `obj:datetime.date` instance.

    If the value cannot be safely converted to a `obj:datetime.date`
    instance, a ValueError will be raised.

    Args:
        value (`obj:datetime.datetime`, `obj:datetime.date` or `obj:str)
            The value that should be converted to a `obj:datetime.date`
            instance.
    """
    if type(value) is datetime.datetime:
        return value.date()
    elif type(value) is datetime.date:
        return value
    elif isinstance(value, str):
        try:
            value = parser.parse(value)
        except ValueError:
            raise ValueError(
                "The provided value cannot be converted to a "
                "datetime.datetime instance."
            )
        else:
            return value.date()
    else:
        # A work around to allow our tests to use this logic in the presence
        # of pytest-freezegun.  pytest-freezegun works by replacing the datetime
        # module with it's own implementation.
        if (settings.ENVIRONMENT == Environments.TEST
                and datetime.datetime.__class__.__name__ == "FakeDatetimeMeta"):
            return value.date()
        raise ValueError(
            "Invalid value %s supplied - cannot convert to datetime." % value)

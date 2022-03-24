from datetime import datetime, timedelta

from django.utils import timezone
from factory.fuzzy import FuzzyNaiveDateTime


class PastDateTimeField(FuzzyNaiveDateTime):
    """
    A DjangoModelFactory field that selects a random date in the past.
    """

    def __init__(self, *args, **kwargs):
        end_value = datetime.now()
        start_value = kwargs.pop('start_value', end_value - timedelta(
            days=kwargs.pop('horizon', 365 * 2)))
        if start_value >= end_value:
            raise ValueError("The start_value must be in the past.")
        super().__init__(start_value, end_value, *args, **kwargs)

    def fuzz(self):
        value = super().fuzz()
        tz = timezone.get_current_timezone()
        return tz.localize(value)


class FutureDateTimeField(FuzzyNaiveDateTime):
    """
    A DjangoModelFactory field that selects a random date in the future.
    """

    def __init__(self, *args, **kwargs):
        start_value = datetime.now()
        end_value = kwargs.pop('end_value',
            start_value + timedelta(days=kwargs.pop('horizon', 365 * 2)))
        if start_value >= end_value:
            raise ValueError("The end_value must be in the future.")
        super().__init__(start_value, end_value, *args, **kwargs)

    def fuzz(self):
        value = super().fuzz()
        tz = timezone.get_current_timezone()
        return tz.localize(value)


class FuzzyPastDateTimeStringField(PastDateTimeField):
    def fuzz(self):
        value = super().fuzz()
        return str(value)


class NowDateTimeField(FuzzyNaiveDateTime):
    """
    Override the .fuzz() method for generating random dates to always return
    the current datetime.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(datetime.now(), *args, **kwargs)

    def fuzz(self):
        return timezone.now()

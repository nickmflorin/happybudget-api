from django.urls import reverse
from django.utils.functional import SimpleLazyObject


def lazy_reverse(*args, **kwargs):
    def get_url(*a, **kw):
        return reverse(*a, **kw)
    return SimpleLazyObject(lambda: get_url(*args, **kwargs))

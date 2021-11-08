import functools
import logging

from django.conf import settings
from django.core.cache import cache

from rest_framework import response, status


logger = logging.getLogger('greenbudget')


def raise_if_not_enabled(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if not settings.CACHE_ENABLED:
            raise Exception("Cache is not enabled.")
        return func(*args, **kwargs)
    return decorator


def request_can_be_cached(request):
    """
    Returns whether or not the request is allowed to be cached based on the
    query parameters on the request.

    Right now, we cannot cache any responses where the GET request included
    query parameters.  This is because this would require invalidating those
    cached responses when certain conditions are met, and we cannot invalidate
    those caches if we do not know what the key is ahead of time.

    We should investigate ways to improve this in the future, because this
    will prevent us from cacheing search results, ordering results and filtering
    results.
    """
    if request.query_params:
        if len(request.query_params) == 1 \
                and request.query_params.get('search') == "":
            return True
        return False
    return True


class endpoint_cache:
    def __init__(self, id, entity, method, prefix=None):
        self.id = id
        self.entity = entity
        self._method = method
        self._prefix = prefix

    def __call__(self, get_key_from_view):
        def decorator(cls):
            original_method = getattr(cls, self._method)
            setattr(cls, self._method, self.decorated_func(
                func=original_method,
                get_key_from_view=get_key_from_view
            ))
            return cls
        return decorator

    def __str__(self):
        return self.id

    def decorated_func(self, func, get_key_from_view):
        @functools.wraps(func)
        def decorated(instance, request, *args, **kwargs):
            # In certain environments, we do not want the cache to be enabled.
            if not settings.CACHE_ENABLED:
                return func(instance, request, *args, **kwargs)

            # Right now, we cannot cache any responses where the GET request
            # included query parameters.  This is because this would require
            # invalidating those cached responses when certain conditions are
            # met, and we cannot invalidate those caches if we do not know what
            # the key is ahead of time.  We should investigate ways to improve
            # this in the future, because this  will prevent us from cacheing
            # search results, ordering results and filtering results.
            if not request_can_be_cached(request):
                return func(instance, request, *args, **kwargs)

            cache_key = get_key_from_view(instance)
            cache_key = self.prefix_key(cache_key)

            data = cache.get(cache_key)
            if data:
                logger.debug("Returning cached value at %s." % cache_key)
                return response.Response(data, status=status.HTTP_200_OK)

            r = func(instance, request, *args, **kwargs)
            cache.set(cache_key, r.data, settings.CACHE_EXPIRY)
            return r
        return decorated

    def invalidate(self, key, log=True):
        if not settings.CACHE_ENABLED:
            return
        cache_key = self.prefix_key(key)
        if log:
            logger.debug("Invalidating Cache %s." % self)
        cache.delete(cache_key)

    @raise_if_not_enabled
    def prefix_key(self, key):
        if self._prefix is not None:
            if not self._prefix.endswith('-'):
                return f'{self._prefix}-{key}'
            return f'{self._prefix}{key}'
        return key


class detail_cache(endpoint_cache):
    def invalidate(self, instance):
        instances = instance if isinstance(instance, (list, tuple)) \
            else [instance]
        for obj in instances:
            logger.debug(
                "Invalidating Cache %s for Instance %s."
                % (self, obj.pk)
            )
            return super().invalidate(obj.pk, log=False)

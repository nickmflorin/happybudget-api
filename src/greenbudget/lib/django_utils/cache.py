import functools
import inspect
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


class endpoint_cache:
    def __init__(self, method):
        self._method = method

    def __call__(self, cls):
        return self.decorate(cls)

    def invalidate(self, key):
        if not settings.CACHE_ENABLED:
            return
        logger.debug("Invalidating Cache %s." % self)
        cache.delete(key)

    def request_can_be_cached(self, request):
        # In certain environments, we do not want the cache to be enabled.
        return settings.CACHE_ENABLED

    def decorate(self, cls, **kwargs):
        original_method = getattr(cls, self._method)
        setattr(cls, self._method, self.decorated_func(
            func=original_method,
            **kwargs
        ))
        return cls

    def decorated_func(self, func, post_cache_args=None):
        @functools.wraps(func)
        def decorated(instance, request, *args, **kwargs):
            if not self.request_can_be_cached(request):
                return func(instance, request, *args, **kwargs)

            arg_mapping = {
                'view': instance,
                'request': request
            }

            if request.user.id is None:
                raise Exception(
                    "Cacheing can only be used on authenticated views.")

            cache_key = f"{request.user.id}-{request.method}-{request.path}"
            if request.query_params:
                cache_key += request.query_params.urlencode()

            data = cache.get(cache_key)
            if data:
                logger.debug("Returning cached value at %s." % cache_key)
                return response.Response(data, status=status.HTTP_200_OK)

            r = func(instance, request, *args, **kwargs)
            cache.set(cache_key, r.data, settings.CACHE_EXPIRY)

            post_cache_arguments = {'cache_key': cache_key}
            if post_cache_args is not None:
                for pcarg in post_cache_args:
                    if hasattr(pcarg[1], '__call__'):
                        arguments = [
                            arg_mapping[ag]
                            for ag in inspect.getfullargspec(pcarg[1]).args
                            if ag in arg_mapping
                        ]
                        post_cache_arguments[pcarg[0]] = pcarg[1](*tuple(arguments))  # noqa
                    else:
                        post_cache_arguments[pcarg[0]] = pcarg[1]

            self.post_cache(**post_cache_arguments)
            return r
        return decorated


class invariant_cache(endpoint_cache):
    def __init__(self, *args, **kwargs):
        self._cached = set([])
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self._key)

    def post_cache(self, cache_key):
        self._cached.add(cache_key)

    def invalidate(self):
        for key in self._cached:
            super().invalidate(key)


class instance_cache(endpoint_cache):
    def __init__(self, entity, method, **kwargs):
        self.entity = entity
        self._cached = {}
        super().__init__(method, **kwargs)

    def __call__(self, get_instance_from_view):
        def decorator(cls):
            return self.decorate(
                cls, post_cache_args=[('pk', get_instance_from_view)])
        return decorator

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.entity)

    def post_cache(self, pk, cache_key):
        self._cached.setdefault(pk, set([]))
        self._cached[pk].add(cache_key)

    def invalidate(self, instance):
        instances = instance if isinstance(instance, (list, tuple, set)) \
            else [instance]
        for obj in instances:
            if obj.id in self._cached:
                for full_cache_key in self._cached[obj.id]:
                    super().invalidate(full_cache_key)
                del self._cached[obj.id]

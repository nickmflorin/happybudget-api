import collections
import contextlib
import functools
import logging
import threading

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

from rest_framework import response, status

from greenbudget.conf import Environments
from greenbudget.lib.utils import ensure_iterable, concat

from greenbudget.app.user.models import User


logger = logging.getLogger('greenbudget')


DATABASE_ENGINE = 'django.core.cache.backends.db.DatabaseCache'
LOCMEM_ENGINE = 'django.core.cache.backends.locmem.LocMemCache'


def is_engine(engine, environments=None, strict=False):
    """
    Returns whether or not the cache backend configured in settings is of the
    specific engine.  If `strict` is `True`, instead of returning `false` an
    Exception will be raised.

    Optionally will raise an exception if the current environment is not allowed
    for the given engine.
    """
    environments = environments or ()
    # We need to access the CACHES inside a function scope just in case the
    # CACHE settings are overridden in tests.
    backend = settings.CACHES["default"]["BACKEND"]
    evaluated_engine = backend == engine
    if evaluated_engine and environments \
            and settings.ENVIRONMENT not in environments:
        raise Exception(
            f"Using {engine} in ${settings.ENVIRONMENT} environment is "
            "prohibited!"
        )
    elif strict and not evaluated_engine:
        raise Exception(f"Engine is not {engine}.")
    return evaluated_engine


def is_database_engine(**kwargs):
    return is_engine(engine=DATABASE_ENGINE, **kwargs)


def is_locmem_engine(**kwargs):
    return is_engine(engine=LOCMEM_ENGINE, **kwargs)


InstancePath = collections.namedtuple('InstancePath', ['instance', 'path'])
EngineeredCacheKey = collections.namedtuple('CacheKey', ['instance', 'key'])

PathConditional = collections.namedtuple(
    'PathConditional', ['condition', 'path'])
ConditionalPath = collections.namedtuple('ConditionalPath', ['conditions'])


class Registry:
    """
    A maintained registry of the registered instances of :obj:`endpoint_cache`
    in the application.  The :obj:`Registry` is used for temporarily disabling
    caches by their registered ID or disabling all registered caches.
    """

    def __init__(self, caches=None):
        self._caches = caches or []

    @property
    def caches(self):
        return self._caches

    def add(self, ch):
        assert ch.id is not None
        if ch.id in [c.id for c in self._caches]:
            raise Exception("Cannot register caches with the same ID.")
        self._caches.append(ch)

    def get_cache(self, cache_id):
        if cache_id not in [c.name for c in self._caches]:
            raise LookupError("No registered cache with ID %s." % cache_id)
        return [c for c in self._caches if c.id == cache_id][0]


registry = Registry()


class RequestCannotBeCached(Exception):
    pass


class endpoint_cache:
    """
    Class that allows us to configure the way that a cache for a specific
    endpoint should behave and then reference the instance either for decorating
    the view or invalidating the cache.

    Parameters:
    ----------
    id: :obj:`str`
        An ID that can be used to reference the cache - does not necessarily
        have to be unique as it is mostly used for logging purposes.

    path: :obj:`str` or :obj:`lambda`
        Either the string path or a function returning the path that should be
        cached with the :obj:`endpoint_cache` instance.  This path will be
        used to determine whether or not a given request to a view should be
        cached and is used to retrieve the cached result from the cache.

        When request paths correspond to a specific model instance, which is
        not known ahead of time, the `path` can be provided as a callback that
        takes the model instance as it's first and only argument.

    dependency: :obj:`tuple` or :obj:`list` or :obj:`lambda` (optional)
        An iterable of dependencies or a single dependency that should also
        be used to invalidate subsequent caches when this :obj:`endpoint_cache`
        is invalidated.

        We define a cache dependency either as a callback that takes the
        instance as it's first and only argument (applicable for caches with
        paths that depend on an instance only) or another :obj:`endpoint_cache`
        instance that should be invalidated after the current instance is.

        Default: []

    disabled: :obj:`bool` (optional)
        Whether or not the cache should be disabled.  Used for simply turning
        off single problematic caches instead of the entire cache framework
        via settings.

        Default: False

    Explanation on Cache Behavior for Different Engines

    Mimicking production cache behavior in tests and locally is a little bit of
    a tricky conundrum, because we have to use different cache engines for each
    environment and different cache engines have slightly different behaviors,
    in particular, around the usage of wildcards.

    Wildcards
    ---------
    Assume that we are dealing with a cache in regard to the detail endpoint
    of a :obj:`Budget` with ID 1:

    >>> cache_key = '<user_id>-GET-/v1/budgets/1/<query_params>'

    We use wildcard patterns for cache key invalidation in the following use
    cases:

    (1) Request Query Params
        If a response is cached where the request included query parameters, we
        want to be able to invalidate that cached response at the same time that
        we would invalidate the cached response for a request without query
        parameters.

        This is because query parameters typically are used for filtering,
        ordering, etc. - and to be safe, if the response without query
        parameters needs to be invalidated due to a change then the response
        with query parameters should almost always also need to be invalidated.

        >>> cache_key = '<user_id>-GET-/v1/budgets/1/*'

    (2) User
        Every cached response is cached only for the user making the request,
        which is important because otherwise one user might received a cached
        response from another user's request.

        When invalidating the cache in the application, there are many times
        when we do not have access to the user who made the request that is in
        context, so we use a middleware class to set the request on this class
        when a request is received via the API.

        However, there are cases where the invalidation will be attempted
        outside the scope of an active request, which can happen in management
        commands, from the Django shell or even in tests.  In this case, in
        order to be safe, we have to rely on a fallback option: invalidating the
        cached endpoint for all users using a wildcard in place of the user ID.

        >>> cache_key = '*-GET-/v1/budgets/1/*'

    Engines
    -------
    The differences in the cache behavior around wildcard ('*') usage for
    pattern matching during cache key validation is the source of the
    difficulties involved with using different cache engines in different
    environments.  The cache engines that we use across our environments are
    as follows:

    (1) Redis Cache with AWS ElasticCache
        - External
        - Supports wildcard pattern matching for cache invalidation.
        - Fast
        - Used in production/development environments.

    (2) LocMemCache
        - Local
        - Does not support wildcard pattern matching for cache invalidation.
        - Faster than DatabaseCache but obviously slower than AWS ElasticCache.
        - Wildcard pattern matching cannot be "mocked" easily.
        - Used for local environments.

    (3) DatabaseCache
        - Local
        - Does not support wildcard pattern matching for cache invalidation.
        - Slower than LocMemCache.
        - Wildcard pattern matching can be "mocked" via usage of the SQL `LIKE`
          operator.
        - Used for test environments.

    In a production/development environment, we use AWS's ElasticCache with a
    redis engine, but we cannot do that locally unless we decided to run a redis
    queue alongside the app (which we may do in the future).  The differences in
    the cache behavior around wildcard ('*') usage for the above engines is the
    source of the difficulty in using consistent cache functionality across
    environments:

    Environments:
    ------------
    Details & caveats of the cache implementation differs from both engine to
    engine and environment to environment:

    (1) Production/Development
        In a production/development environment, pattern matching via the Redis
        cache engine is supported - so we do not have to worry about mocking it.
        However, we do have to be concerned with cases where the invalidation
        is being done when the request is not in scope (i.e. from the shell or
        management commands).  In this case, we need to log a warning and
        invalidate the cache for all users.

    (2) Local
        In a local environment, pattern matching is not suported.  This means
        that we cannot use wildcards in place of unknown users or query
        parameters.  As a result, in order to as closely as possible mimic
        production behavior, we do not include the following in cache keys:

        (a) Query Parameters
            The implication of this is simply that a request to an endpoint
            with query parameters will not be cached.  This is not a big deal,
            it just makes some requests a tad slower locally.

        (b) User IDs
            The implication of this is simply that a request to an endpoint is
            cached regardless of the user making the request.  This is not a
            big deal, because you can only ever have one user using the
            application at a time in a local environment.
            Because we are not using wildcards for user IDs, we do not have
            to be concerned with cache invalidation outside the scope of a
            request (from management commands or the shell).

    (3) Test
        In a test environment, pattern matching is not supported but is mocked
        via usage of the SQL `LIKE` operator.  This allows the test environment
        to more closely match the cache beahvior of a production environment
        than the cache behavior in the local environment does.

        The only caveat is if performing actions outside the scope of a request
        in a test, the request will not be set on this class via the middleware
        and a wildcard operator will be used.

        This again is not a big deal, as tests are *usually* run with only
        one user logged in - but just in case, we expose a test utility to
        manually set the request on this class.
    """
    method = "GET"
    thread = threading.local()

    def __init__(self, cache_id, path, dependency=None, disabled=False):
        self.id = cache_id
        self._path = path
        self._dependency = dependency

        self._disabled = False
        self._hard_disabled = disabled
        registry.add(self)

    def __call__(self, cls):
        return self.decorate(cls)

    @property
    def disabled(self):
        return not settings.CACHE_ENABLED or self._disabled \
            or self._hard_disabled

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.id)

    @property
    def dependencies(self):
        return ensure_iterable(self._dependency)

    def request_can_be_cached(self, request):
        if request.method.upper() != self.method.upper():
            return False
        return not self.disabled

    @contextlib.contextmanager
    def with_disable(self):
        self._disabled = True
        try:
            yield self
        finally:
            self._disabled = False

    def disable(self, *args):
        """
        A decorator or context manager that will temporarily disable this
        :obj:`endpoint_cache` instance inside the decorated function or
        inside of the context.
        """
        if len(args) == 1 and hasattr(args[0], '__call__'):
            func = args[0]

            @functools.wraps(func)
            def decorated(*args, **kwargs):
                with self.with_disable():
                    return func(*args, **kwargs)
            return decorated
        return self.with_disable()

    def decorate(self, cls):
        setattr(cls, 'dispatch', self.decorated_func(cls.dispatch))
        return cls

    def _format_path(self, path):
        assert path.endswith('/'), \
            "The request path must end with a trailing slash."
        assert path.startswith('/'), \
            "The request path must start with a trailing slash."
        if not path.startswith('/v1'):
            return f"/v1{path}"
        return path

    def _call_path(self, instance, path_caller):
        # We need to make sure that the instance still has an ID before
        # reconstructing the path.  This can happen in cases where we are
        # invalidating detail caches after their associated instances are
        # deleted.
        if instance.pk is None:
            raise Exception(
                f"Cache {self.id} for instance {instance.__class__.__name__} "
                "cannot be invalidated because the instance does not have an "
                "ID."
            )
        path = path_caller(instance)
        return self._format_path(path)

    def _instance_paths(self, instance=None, path=None):
        """
        Returns an array of request paths that are reverse engineered based
        on an optionally provided instance or instances.  The paths are
        reverse engineered based on the `path` parameter provided to the cache
        on initialization.
        """
        instances = ensure_iterable(instance)
        path = path or self._path

        assert isinstance(self._path, str) or callable(self._path) \
            or isinstance(self._path, ConditionalPath), \
            "The cache request path must be a string, a callable taking " \
            "the instance as it's first and only argument, or an instance of " \
            "ConditionalPath."

        if isinstance(path, ConditionalPath):
            instance_paths = []
            for condition in self._path.conditions:
                instances_meeting_condition = [
                    obj for obj in instances
                    if condition.condition(obj)
                ]
                instance_paths += self._instance_paths(
                    instance=instances_meeting_condition,
                    path=condition.path
                )
            return instance_paths

        elif callable(path):
            assert instance is not None, \
                "If the request path is a callable, the instance must be " \
                "provided in the case that the request is not in scope."
            return [
                InstancePath(
                    instance=obj,
                    path=self._format_path(self._call_path(obj, path))
                ) for obj in instances
            ]
        assert instance is None, \
            "The instance should not be provided when the cached request path " \
            "is not dependent on one."
        return [InstancePath(
            instance=None,
            path=self._format_path(path)
        )]

    def _invalidate(self, key):
        # Invalidating a single key is separated from the invalidation of
        # multiple keys to make it easier to monkeypatch in tests.
        if self.disabled:
            return
        logger.debug("Invalidating Cache %s at Key %s" % (self, key.key))
        cache.delete(key.key)

    def invalidate(self, *args, **kwargs):
        if self.disabled:
            return
        ignore_deps = kwargs.pop('ignore_deps', False)
        key = self.get_cache_key(*args, **kwargs)
        for keyi in key:
            self._invalidate(keyi)
            if not ignore_deps:
                for dep in [d for d in self.dependencies
                        if not isinstance(d, self.__class__)]:
                    dep(keyi.instance)
        if not ignore_deps:
            for dep in [d for d in self.dependencies
                    if isinstance(d, self.__class__)]:
                dep.invalidate(*args, **kwargs)

    def _raw_cache_key(self, path, user=None, query=None, wildcard=False):
        # Requests need to be cached on a user basis, so if the user is not
        # authenticated we cannot cache the request.
        if isinstance(user, AnonymousUser):
            # If the user is not authenticated, we do not want to raise an
            # exception - because we need to allow the force logout process
            # to proceed via the middleware.
            raise RequestCannotBeCached()

        if not wildcard:
            cache_key = f"{self.method}-{path}"
            if user:
                # The user can be a wildcard in the case that the invalidation
                # is being performed outside the scope of a request.
                assert isinstance(user, User) or user == "*"
                cache_key = f"{getattr(user, 'id', user)}-{cache_key}"
            if query:
                cache_key += f"?{query.urlencode()}"
            return cache_key
        # The wildcard is used in place of query parameters, when we are
        # reverse engineering the cache key during invalidation (and do not
        # know what the query parameters are because there is no request).
        assert query is None, "A wildcard cannot be used with query parameters."
        key = self._raw_cache_key(path, user=user)
        return [key, f"{key}?*"]

    def request_cache_key(self, request):
        # Enforce that we are cacheing the request or using the cached
        # response only for GET requests.
        assert request.method.upper() == self.method, \
            f"Requests of method ${request.method} cannot be cached."

        # Since we are obtaining the cache key for a request, the request should
        # be in the active context on this class and should be set on the
        # thread.
        assert request.user == self.thread.request.user, \
            "Middleware is not properly associating the request with the " \
            "cache implementation."

        if is_locmem_engine(environments=[
                Environments.LOCAL, Environments.TEST]):
            # When using a LocMemCache, wildcard supporting is not allowed.
            # This means that we cannot cache requests with query params at all
            # - because we would have no means of invalidating them when the
            # request path without query parameters was invalidated, and we
            # cannot cache request by user because we would not be able to
            # invalidate against wildcard * users.  However, the latter is okay,
            # for local development, because we do not need to be concerned with
            # multiple users sending requests simultaneously.
            if request.query_params is not None:
                raise RequestCannotBeCached()
            # Return a cache-key that is not dependent on the user - we can
            # only do this since we are guaranteed to be in a local environment.
            return self._raw_cache_key(path=request.path)
        return self._raw_cache_key(
            path=request.path,
            user=request.user,
            query=request.query_params
        )

    def engineered_cache_keys(self, instance=None):
        paths = self._instance_paths(instance=instance)
        if getattr(self.thread, 'request', None) is None:
            # LocMemCache does support indexing cached responses by user so we
            # do not need to worry about issuing a warning.
            if not is_locmem_engine(
                    environments=[Environments.LOCAL, Environments.TEST]):
                logger.warning(
                    "Cannot obtain user from active request because the cache "
                    "is being invalidated outside the scope of an API request. "
                    "This means that we have to invalidate the cache for all "
                    "users to be safe.", extra={'paths': paths}
                )
                return concat([[
                    EngineeredCacheKey(instance=p.instance, key=k)
                    for k in self._raw_cache_key(
                        path=p.path, user='*', wildcard=True)
                ] for p in paths])

            # If using the LocMemCache, then we did not cache the request by
            # the user to begin with.
            return concat([[
                EngineeredCacheKey(instance=p.instance, key=k)
                for k in self._raw_cache_key(path=p.path, wildcard=True)
            ] for p in paths])

        return concat([[
            EngineeredCacheKey(instance=p.instance, key=k)
            for k in self._raw_cache_key(
                path=p.path, user=self.thread.request.user, wildcard=True)
        ] for p in paths])

    def _cache_key(self, path, user='*', wildcard=False, query=None):
        # Requests need to be cached on a user basis, so if the user is not
        # authenticated we cannot cache the request.
        if isinstance(user, AnonymousUser):
            raise Exception(
                "Endpoints can only be cached for authenticated users.")

        # The user can be a wildcard in the case that the invalidation is being
        # performed outside the scope of a request.
        assert isinstance(user, User) or user == "*"

        if not wildcard:
            # When using a LocMemCache, wildcard supporting is not allowed - so
            # we cannot cache requests on a per-user basis, and we cannot cache
            # any requests with query parameters.
            if is_locmem_engine(environments=[
                    Environments.LOCAL, Environments.TEST]):
                return [f"{self.method}-{path}"]
            # Allow user to be provided as User object or ID.
            user_component = getattr(user, 'id', user)
            assert isinstance(user_component, (int, str))
            cache_key = f"{user_component}-{self.method}-{path}"
            if query:
                cache_key += f"?{query.urlencode()}"
            return [cache_key]

        # The wildcard is used in place of query parameters, when we are
        # reverse engineering the cache key during invalidation (and do not
        # know what the query parameters are because there is no request).
        assert query is None, "A wildcard cannot be used with query parameters."
        key = self._cache_key(path, user=user)
        return [key[0], f"{key[0]}?*"]

    def get_cache_key(self, *args, **kwargs):
        """
        Returns the cache key (before it is formatted via Django's
        `make_cache_key` method) for a given request or invalidation routine.

        The cache key needs to be capable of being created in two contexts:

        (1) Get/Set Context:
            This happens inside of the dispatch method where the request is
            available.  In this context:

            (a) The user is obtained from the request.
            (b) The cache key is generated solely from the request.

        (2) Invalidate Context:
            This happens outside of the dispatch method where the request is not
            available.  In this context:

            (a) The user is obtained from the request set on the class via
                the corresponding middleware, or is explicitly provided as an
                argument.
            (b) The cache key is reverse engineered based on the user and a
                provided instance (if applicable for the endpoint).

            Since we do not always have access to the :obj:`User` associated with
            a given need to invalidate a cache key, we use the middleware class
            :obj:`greenbudget.app.middleware.CacheUserMiddleware` to set the
            request on this class whenever a request is received via the API.

            In the case that the request is not set on this class, the
            invalidation is either being triggered from a management command,
            the shell or a test - all outside the scope of an active request.
            In these cases, we have to assume that we need to be safe and
            invalidate the cache for all users.
        """
        request = kwargs.pop('request', None)
        if request is not None:
            return self.request_cache_key(request)

        # Cache key needs to be reverse engineered from the `path` argument
        # supplied on initialization and an optionally provided set of instances
        # or a single instance (in the case that the request path pertains to
        # a specific instance). There can be multiple paths, and thus multiple
        # keys, associated with a given invalidation routine if there are
        # multiple instances passed in.
        instance = args[0] if args else kwargs.pop('instance', None)
        return self.engineered_cache_keys(instance=instance)

    def get(self, request):
        # Since we are creating the cache key from the request, and not an
        # instance (or an iterable of instances) there should only be 1
        # cache key returned.
        cache_key = self.get_cache_key(request=request)
        data = cache.get(cache_key)
        if data:
            logger.debug("Returning cached value at %s." % cache_key)
        return data

    def set(self, request, rsp):
        try:
            cache_key = self.get_cache_key(request=request)
        except RequestCannotBeCached:
            return
        cache.set(cache_key, rsp.data, settings.CACHE_EXPIRY)

    def decorated_func(self, func):
        """
        In order to systematically return cached responses if certain critiria
        are met, we need to wrap the logic on instances of
        :obj:`rest_framework.views.APIView` such that the method that is
        responsible for returning the response is only used in the case that
        there is not a cached response.

        There can be many different methods on the view that are responsible
        for this, and the method chosen (whether it be get, retrieve, list,
        post, patch, etc.) depends on the URL path and the request method.

        The problem is that our cache system recognizes whether or not a certain
        request to the view should use a cached response based on the request
        path (and enforces the request method is GET).  Since we cannot easily
        reverse engineer the request path to the method on the view responsible
        for returning the response, especially when you consider usage of
        @decorators.action methods, we have to override the source dispatch
        method that all response handler methods funnel into, namely: "dispatch".
        """

        def dispatch_routine(view, request, *args, **kwargs):
            """
            A modified version of rest_framework's `dispatch` method on
            :obj:`rest_framework.views.APIView`.  This modified version differs
            by using the cached response (provided as a keyword argument)
            instead of the method on the view dictated by the request method.
            """
            rsp = kwargs.pop('response')
            try:
                view.initial(request, *args, **kwargs)
                # Here, traditional rest_framework's dispatch method would
                # call the associated method on the view (whether it be
                # get, post, patch, etc.) to get the response.
            # pylint: disable=broad-except
            except Exception as exc:
                # Instead of returning the response, we now have to allow DRF
                # to handle the exception.
                rsp = view.handle_exception(exc)
            view.response = view.finalize_response(request, rsp, *args, **kwargs)
            return view.response

        @functools.wraps(func)
        def dispatch(view, request, *args, **kwargs):
            """
            Overrides rest_framework's `dispatch` method on
            :obj:`rest_framework.views.APIView` such that the traditional
            dispatch method behavior is only called when there is not already
            a cached response.

            If there is a cached response, the modified dispatch method above is
            used, such that we encapsulate the behavior of the traditional
            dispatch method with the exception that the response is obtained
            from the cache.
            """
            if not self.request_can_be_cached(request):
                return func(view, request, *args, **kwargs)

            # Even though this is just performed in the traditional dispatch
            # routine, we need to perform this regardless of whether or not
            # we are fully overriding the dispatch method because the cache
            # key needs the request query parameters, which will not be on the
            # request until this is performed.
            view.args = args
            view.kwargs = kwargs
            modified_request = view.initialize_request(request, *args, **kwargs)
            view.request = modified_request
            # This may be deprecated by DRF.
            view.headers = view.default_response_headers

            try:
                data = self.get(modified_request)
            except RequestCannotBeCached:
                # Do not call the original dispatch method with the modified
                # request.
                return func(view, request, *args, **kwargs)
            if data:
                # It is safe to assume that the response status code should be
                # 200 because cacheing is only allowed currently for GET
                # requests.
                kwargs['response'] = response.Response(
                    data, status=status.HTTP_200_OK)
                return dispatch_routine(view, modified_request, *args, **kwargs)
            # Do not call the original dispatch method with the modified request.
            r = func(view, request, *args, **kwargs)
            self.set(modified_request, r)
            return r

        return dispatch


class disable(contextlib.ContextDecorator):
    """
    Context manager or function decorator that will temporarily disable
    :obj:`endpoint_cache` instance(s) inside of the context or inside of the
    function implementation.

    Parameters:
    ----------
    signals: :obj:`list` or :obj:`tuple` or :obj:`Signal` or None
        The specific signal, or iterable of signals, that should be disabled
        inside the context.  Signals can be referenced either by their
        registered name or by the :obj:`Signal` instance itself.  If no
        :obj:`Signal`(s) are provided, all :obj:`Signal`(s) will be disabled
        in the context.

        Default: None
    """

    def __init__(self, **kwargs):
        # Caches that should be disabled in context, either identified by
        # their ID in the registry or the :obj:`endpoint_cache` instance.  If
        # not provided, all caches in the registry will be disabled in
        # context.
        self._caches = kwargs.pop('signals', None)
        super().__init__()

    @property
    def caches(self):
        if not self._caches:
            return registry.caches
        cache_instances = []
        for c in ensure_iterable(self._caches):
            if isinstance(c, str):
                cache_instances.append(registry.get_cache(c))
            else:
                cache_instances.append(c)
        return cache_instances

    def __enter__(self):
        for c in self.caches:
            c._disabled = True
        return self

    def __exit__(self, *exc):
        for c in self.caches:
            c._disabled = False
        return False

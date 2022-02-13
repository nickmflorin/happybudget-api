from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from .cache import endpoint_cache
from .model import model


class ModelRequestMiddleware(MiddlewareMixin):
    """
    Middleware that associates the user associated with the incoming HTTP
    request with the :obj:`model` so that the user performing the alteration to
    the model can be referenced.
    """

    def process_request(self, request):
        model.thread.request = request


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware that bypasses Django's ALLOWED_HOSTS setting such that the
    AWS Load Balancer(s) can perform health checks with a dynamic IP address.
    """

    def process_request(self, request):
        if request.META["PATH_INFO"] == "/":
            return HttpResponse("Healthy")


class CacheUserMiddleware(MiddlewareMixin):
    """
    Middleware that associates the user associated with the incoming HTTP
    request with the :obj:`endpoint_cache` so that the caches can be invalidated
    on a per-user basis.
    """

    def process_request(self, request):
        endpoint_cache.thread.request = request

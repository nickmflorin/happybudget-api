from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware that bypasses Django's ALLOWED_HOSTS setting such that the
    AWS Load Balancer(s) can perform health checks with a dynamic IP address.
    """

    def process_request(self, request):
        if request.META["PATH_INFO"] == "/":
            return HttpResponse("Healthy")

from django.utils.deprecation import MiddlewareMixin

from .models import model


class ModelSignalMiddleware(MiddlewareMixin):
    """
    Middleware that associates the user associated with the incoming HTTP
    request with the :obj:`model` so that the user performing the alteration to
    the model can be referenced.
    """

    def process_request(self, request):
        model.thread.request = request

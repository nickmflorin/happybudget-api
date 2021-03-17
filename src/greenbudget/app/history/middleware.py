from django.utils.deprecation import MiddlewareMixin

from .tracker import ModelHistoryTracker


class ModelHistoryMiddleware(MiddlewareMixin):
    """
    Middleware that associates the incoming HTTP request with the
    :obj:`ModelHistoryTracker` so that the user performing the alteration
    to the model can be referenced.
    """

    def process_request(self, request):
        ModelHistoryTracker.thread.request = request

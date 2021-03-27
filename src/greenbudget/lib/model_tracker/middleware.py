from django.utils.deprecation import MiddlewareMixin

from .track_model import track_model


class TrackModelMiddleware(MiddlewareMixin):
    """
    Middleware that associates the incoming HTTP request with the
    :obj:`track_model` so that the user performing the alteration
    to the model can be referenced.
    """

    def process_request(self, request):
        track_model.thread.request = request

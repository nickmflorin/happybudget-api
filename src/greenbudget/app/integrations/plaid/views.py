from greenbudget.app import views
from .serializers import CreateLinkTokenSerializer


class PlaidLinkTokenView(
    views.CreateModelMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /integrations/plaid/link-token/
    """
    serializer_class = CreateLinkTokenSerializer

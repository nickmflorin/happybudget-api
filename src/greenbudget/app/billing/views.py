import logging

from rest_framework import mixins, response, status

from greenbudget.lib.django_utils.cache import endpoint_cache

from greenbudget.app import views
from greenbudget.app.user.serializers import UserSerializer

from .exceptions import StripeBadRequest
from .permissions import (
    IsStripeCustomerPermission,
    IsNotStripeCustomerPermission
)
from .serializers import (
    StripeProductSerializer,
    UserCheckoutSessionSerializer,
    UserSyncStripeSerializer,
    UserPortalSessionSerializer,
    StripeSubscriptionSerializer
)
from .stripe_client import get_products
from . import stripe


logger = logging.getLogger('greenbudget')


class StripeSessionViewSet(mixins.CreateModelMixin, views.GenericViewSet):
    def pre_response(self, session, request):
        return

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        self.pre_response(session, request)
        return response.Response({"redirect_url": session.url})


class CheckoutSessionViewSet(StripeSessionViewSet):
    serializer_class = UserCheckoutSessionSerializer
    extra_permission_classes = [IsNotStripeCustomerPermission]

    def pre_response(self, session, request):
        # We want to include the session ID on the session so after the checkout
        # is being finalized, we can tell the difference that endpoint being
        # accessed after the FE redirect from Stripe or a user incidentally
        # visiting the Checkout Success page.  This allows us to distinguish
        # between actual errors that occur in the checkout process and false
        # positives.
        request.session["session_id"] = session.id


class PortalSessionViewSet(StripeSessionViewSet):
    serializer_class = UserPortalSessionSerializer
    extra_permission_classes = [IsStripeCustomerPermission]


class SyncCheckoutSessionViewSet(mixins.CreateModelMixin, views.GenericViewSet):
    serializer_class = UserSyncStripeSerializer
    extra_permission_classes = [IsNotStripeCustomerPermission]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return response.Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK
        )


class SubscriptionView(mixins.RetrieveModelMixin, views.GenericViewSet):
    serializer_class = StripeSubscriptionSerializer

    def get_object(self, *args, **kwargs):
        if self.request.user.stripe_id is None:
            return None
        try:
            return self.request.user.stripe_customer.subscription
        except stripe.error.InvalidRequestError as e:
            logger.error(
                "Stripe HTTP Error: Could not retrieve subscription for user "
                "%s." % self.request.user.pk, extra={
                    'user_id': self.request.user.pk,
                    'email': self.request.user.email,
                    "error": e.error.to_dict_recursive(),
                    "request_id": e.request_id
                })
            raise StripeBadRequest()

    def retrieve(self, request, *args, **kwargs):
        subscription = self.get_object()
        data = None
        if subscription is not None:
            data = self.serializer_class(subscription).data
        return response.Response(
            {"subscription": data}, status=status.HTTP_200_OK)


@endpoint_cache(method="list")
class ProductView(mixins.ListModelMixin, views.GenericViewSet):
    serializer_class = StripeProductSerializer

    def get_queryset(self):
        return get_products()

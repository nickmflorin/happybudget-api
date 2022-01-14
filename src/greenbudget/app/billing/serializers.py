import logging
import os

from django.conf import settings
from rest_framework import serializers

from greenbudget.lib.drf.fields import UnixTimestampField
from greenbudget.app.user.models import User

from .exceptions import (
    CheckoutError, StripeBadRequest, CheckoutSessionInactiveError)
from .utils import get_product_internal_id, subscription_status
from . import stripe


logger = logging.getLogger('greenbudget')


class UserSyncStripeSerializer(serializers.ModelSerializer):
    session_id = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )

    class Meta:
        model = User
        fields = ('session_id', )

    def validate(self, attrs):
        request = self.context['request']

        # Permissions should prevent this from happening, but just in case...
        assert request.user.stripe_id is None, \
            "The user cannot have more than one stripe ID."

        # If the session_id is not in the request session, we do not want to
        # issue an error because this can occur if the user incidentally visits
        # the FE /checkout-success route, without having been redirected from
        # Stripe.  The session_id provided in the request should be relied on
        # as the source of truth.
        if "session_id" not in request.session:
            raise CheckoutSessionInactiveError()

        # Security check to ensure that the session_id included in the redirect
        # from Stripe in the FE is the same as the session_id we stored on the
        # request in the backend.
        request_session_id = request.session['session_id']

        # Make sure to remove the checkout_id from the request session since it
        # is no longer valid, and trying to access it again is a sign that
        # something is amiss.
        del request.session['session_id']

        if request_session_id != attrs['session_id']:
            logger.error(
                "Stripe Checkout Error: The session ID from Stripe `%s` is "
                "inconsistent with the session ID stored on the request "
                "session, `%s`.  This is a sign that something is off, and/or "
                "someone is attempting to expose a security hole."
                % (attrs['session_id'], request_session_id), extra={
                    'user_id': request.user.pk,
                    'email': request.user.email,
                    "request_session_id": request_session_id,
                    "stripe_session_id": attrs['session_id']
                })
            raise CheckoutError(
                "Stripe and request session IDs are inconsistent.")

        try:
            session = stripe.checkout.Session.retrieve(attrs['session_id'])
        except stripe.error.InvalidRequestError as exc:
            logger.error(
                "Stripe Checkout Error: Could not find checkout session "
                "associated with `checkout_id = %s` for user %s.  The user "
                "needs to be manually associated with the Stripe Customer ID "
                "that was created via checkout."
                % (attrs['session_id'], request.user.pk), extra={
                    'user_id': request.user.pk,
                    'email': request.user.email,
                    'error': "%s" % exc.error.to_dict_recursive(),
                    "request_id": exc.request_id
                }
            )
            raise CheckoutError(
                "The checkout session could not be retrieved from the session "
                "ID.")

        try:
            client_reference_id = int(session.client_reference_id)
        except ValueError:
            logger.error(
                "Stripe Checkout Error: Could not convert session's "
                "`client_reference_id`, %s, to an integer primary key for "
                "user." % session.client_reference_id, extra={
                    'user_id': request.user.pk,
                    'email': request.user.email,
                }
            )
            raise CheckoutError("Corrupted checkout session.")

        # Extra security check to make sure that the user that created the
        # checkout session is the user that is syncing the checkout session.
        if request.user.id != client_reference_id:
            logger.error(
                "Stripe Checkout Error: The checkout session was created "
                "by a different user, %s, than the one trying to sync with it, "
                "%s.  This is a sign someone may be trying to exploit a "
                "security hole."
                % (session.client_reference_id, request.user.id), extra={
                    'user_id': request.user.pk,
                    'email': request.user.email,
                    'session_user_id': session.client_reference_id,
                    'session_user_email': session.customer_email
                }
            )
            raise CheckoutError(
                "The checkout session was created by a different user than the "
                "currently logged in user."
            )
        elif session.status != "complete":
            raise CheckoutError("Checkout session has not completed processing.")
        return {'stripe_id': session.customer}


class StripeSessionSerializer(serializers.Serializer):
    @property
    def session_type(self):
        raise NotImplementedError()

    def create_session(self, validated_data, request):
        raise NotImplementedError()

    def validate(self, attrs):
        request = self.context['request']
        try:
            session = self.create_session(attrs, request)
        except stripe.error.InvalidRequestError as exc:
            logger.error(
                f"Stripe {self.session_type.upper()} Session Error: "
                f"Received HTTP error creating {self.session_type} session "
                "with Stripe for user %s." % request.user.id, extra={
                    'user_id': request.user.pk,
                    'email': request.user.email,
                    'error': "%s" % exc.error.to_dict(),
                    "request_id": exc.request_id
                }
            )
            raise StripeBadRequest()
        return {"session": session}

    def create(self, validated_data):
        return validated_data["session"]


class UserPortalSessionSerializer(StripeSessionSerializer):
    session_type = "portal"

    def create_session(self, validated_data, request):
        return stripe.billing_portal.Session.create(
            customer=request.user.stripe_id,
            return_url=os.path.join(settings.FRONTEND_URL, "billing")
        )


class UserCheckoutSessionSerializer(StripeSessionSerializer):
    session_type = "checkout"
    price_id = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )

    class Meta:
        fields = ('price_id', )

    def create_session(self, validated_data, request):
        return stripe.checkout.Session.create(
            success_url=os.path.join(
                settings.FRONTEND_URL,
                "billing/checkout-success?sessionId={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=os.path.join(
                settings.FRONTEND_URL,
                "billing/checkout-cancel?sessionId={CHECKOUT_SESSION_ID}"
            ),
            mode='subscription',
            allow_promotion_codes=True,
            client_reference_id="%s" % self.context['user'].pk,
            customer_email=self.context['user'].email,
            line_items=[{
                'price': validated_data['price_id'],
                'quantity': 1,
            }],
        )


class StripeSubscriptionSerializer(serializers.Serializer):
    """
    A :obj:`rest_framework.serializers.Serializer` class to handle the
    serialization of :obj:`stripe.api_resources.product.Product`.
    """
    id = serializers.CharField(read_only=True)
    cancel_at_period_end = serializers.BooleanField(read_only=True)
    canceled_at = UnixTimestampField(read_only=True)
    cancel_at = UnixTimestampField(read_only=True)
    current_period_start = UnixTimestampField(read_only=True)
    current_period_end = UnixTimestampField(read_only=True)
    start_date = UnixTimestampField(read_only=True)
    stripe_status = serializers.CharField(read_only=True)
    status = serializers.SerializerMethodField()

    def get_status(self, instance):
        return subscription_status(instance)


class StripeProductSerializer(serializers.Serializer):
    """
    A :obj:`rest_framework.serializers.Serializer` class to handle the
    serialization of :obj:`stripe.api_resources.product.Product`.
    """
    id = serializers.SerializerMethodField()
    active = serializers.BooleanField(read_only=True)
    description = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    stripe_id = serializers.CharField(read_only=True, source='id')
    image = serializers.SerializerMethodField()
    price_id = serializers.CharField(read_only=True)

    def get_id(self, instance):
        return get_product_internal_id(instance)

    def get_image(self, instance):
        if instance.images:
            return instance.images[0]
        return None

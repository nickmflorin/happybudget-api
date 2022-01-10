from rest_framework import permissions

from greenbudget.app.authentication.exceptions import (
    SubscriptionPermissionError,
    PermissionErrorCodes,
    PermissionError
)


class IsStripeCustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated \
                or request.user.stripe_id is None:
            raise PermissionError("User is not a Stripe customer.")
        return True


class IsNotStripeCustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated \
                or request.user.stripe_id is not None:
            raise PermissionError("User is already a Stripe customer.")
        return True


class BaseSubscriptionPermission(permissions.BasePermission):
    code = PermissionErrorCodes.SUBSCRIPTION_ERROR

    def __init__(self, products='__all__'):
        self._products = products

    @property
    def products(self):
        return self._products

    def permission_denied(self, message=None):
        kwargs = {'products': self.products, 'code': self.code}
        if message is not None:
            kwargs['detail'] = message
        elif hasattr(self, 'message'):
            kwargs['detail'] = self.message
        raise SubscriptionPermissionError(**kwargs)

    def user_has_permission(self, user):
        if not user.is_authenticated \
                or not user.has_product(self.products):
            return False
        return True


class SubscriptionPermission(BaseSubscriptionPermission):
    def has_permission(self, request, view):
        if not self.user_has_permission(request.user):
            self.permission_denied()
        return True

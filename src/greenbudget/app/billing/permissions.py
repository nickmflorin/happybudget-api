from rest_framework import permissions

from greenbudget.app.authentication.exceptions import (
    PermissionErrorCodes,
    PermissionError
)
from .exceptions import ProductPermissionError
from .mixins import ProductPermissionIdMixin


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


class BaseProductPermission(
        ProductPermissionIdMixin, permissions.BasePermission):
    code = PermissionErrorCodes.PRODUCT_PERMISSION_ERROR

    def __init__(self, *args, **kwargs):
        permission_id = kwargs.pop('permission_id', None)
        self._products = kwargs.pop('products', '__any__')
        ProductPermissionIdMixin.__init__(self, permission_id=permission_id)
        permissions.BasePermission.__init__(self, *args, **kwargs)

    @property
    def products(self):
        return self._products

    def permission_denied(self, message=None):
        kwargs = {
            'products': self.products,
            'code': self.code,
            'permission_id': self.permission_id
        }
        if message is not None:
            kwargs['detail'] = message
        elif hasattr(self, 'message'):
            kwargs['detail'] = self.message
        raise ProductPermissionError(**kwargs)

    def user_has_permission(self, user):
        if not user.is_authenticated \
                or not user.has_product(self.products):
            return False
        return True

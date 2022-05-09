from happybudget.app import permissions

from .exceptions import ProductPermissionError
from .mixins import ProductPermissionIdMixin


class BillingPermissionMixin:
    @classmethod
    def default_disabled(cls, s):
        return not s.BILLING_ENABLED


class IsStripeCustomerPermission(
        BillingPermissionMixin, permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated \
                or request.user.stripe_id is None:
            raise permissions.PermissionErr("User is not a Stripe customer.")
        return True


class IsNotStripeCustomerPermission(
        BillingPermissionMixin, permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated \
                or request.user.stripe_id is not None:
            raise permissions.PermissionErr("User is already a Stripe customer.")
        return True


class BaseProductPermission(
    BillingPermissionMixin,
    ProductPermissionIdMixin,
    permissions.BasePermission
):
    code = permissions.PermissionErrorCodes.PRODUCT_PERMISSION_ERROR
    message = (
        "The user does not have the correct subscription to view this "
        "{object_name}."
    )
    exception_class = ProductPermissionError
    exception_kwargs = ['products', 'permission_id']
    user_dependency_flags = ['is_authenticated', 'is_active', 'is_verified']

    def __init__(self, *args, **kwargs):
        permission_id = kwargs.get('permission_id', None)
        self._products = kwargs.get('products', '__any__')
        ProductPermissionIdMixin.__init__(self, permission_id=permission_id)
        permissions.BasePermission.__init__(self, *args, **kwargs)

    @property
    def products(self):
        return self._products

    def user_has_products(self, user):
        return user.has_product(self.products)

from greenbudget.app import permissions

from .exceptions import ProductPermissionError
from .mixins import ProductPermissionIdMixin


class IsStripeCustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated \
                or request.user.stripe_id is None:
            raise permissions.PermissionErr("User is not a Stripe customer.")
        return True


class IsNotStripeCustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated \
                or request.user.stripe_id is not None:
            raise permissions.PermissionErr("User is already a Stripe customer.")
        return True


class BaseProductPermission(
        ProductPermissionIdMixin, permissions.BasePermission):
    code = permissions.PermissionErrorCodes.PRODUCT_PERMISSION_ERROR
    object_name = "object"
    message = (
        "The user does not have the correct subscription to view this "
        "{object_name}."
    )
    exception_class = ProductPermissionError
    exception_kwargs = ['products', 'permission_id']

    def __init__(self, *args, **kwargs):
        permission_id = kwargs.get('permission_id', None)
        self._products = kwargs.get('products', '__any__')
        ProductPermissionIdMixin.__init__(self, permission_id=permission_id)
        permissions.BasePermission.__init__(self, *args, **kwargs)

    @property
    def products(self):
        return self._products

    def user_has_products(self, user):
        assert user.is_authenticated, \
            f"Permission class {self.__class__.__name__} should always be " \
            "preceeded by a permission class that guarantees authentication."
        return user.has_product(self.products)

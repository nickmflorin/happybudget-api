from rest_framework import permissions, exceptions
from greenbudget.lib.utils import ensure_iterable

from .exceptions import ProductPermissionDenied


class IsStripeCustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # This assumes that this permission is always preceeded by the
        # IsAuthenticated permission class, otherwise, we cannot rely on the
        # request user not being an AnonymousUser.
        if request.user.stripe_id is None:
            raise exceptions.PermissionDenied("User is not a Stripe customer.")
        return True


class IsNotStripeCustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # This assumes that this permission is always preceeded by the
        # IsAuthenticated permission class, otherwise, we cannot rely on the
        # request user not being an AnonymousUser.
        if request.user.stripe_id is not None:
            raise exceptions.PermissionDenied(
                "User is already a Stripe customer.")
        return True


class ProductPermission(permissions.BasePermission):
    def __init__(self, products):
        self._products = ensure_iterable(products)

    @property
    def products(self):
        return self._products

    def has_permission(self, request, view):
        if request.user.product_id not in self._products:
            raise ProductPermissionDenied()
        return True


class BudgetCountProductPermission(ProductPermission):
    def __init__(self, products, max_count=1, methods=["POST"], actions=None):
        self._max_count = max_count
        self._request_methods = ensure_iterable(methods)
        self._actions = actions
        super().__init__(products)

    def has_permission(self, request, view):
        if request.method.upper() in self._request_methods \
                and (self._actions is None or view.action in self._actions):
            if request.user.budgets.count() < self._max_count:
                return True
            return super().has_permission(request, view)
        return True

from greenbudget.app import permissions

from greenbudget.app.billing import ProductPermissionId
from greenbudget.app.billing.permissions import BaseProductPermission
from greenbudget.app.template.models import Template

from .models import Budget


class BudgetOwnershipPermission(permissions.AdminPermissionMixin,
        permissions.IsOwner):
    object_name = 'budget'

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Template) and obj.community is True:
            return self.has_admin_permission(request, view)
        return super().has_object_permission(request, view, obj)


class BudgetProductPermission(BaseProductPermission):
    default_permission_id = ProductPermissionId.MULTIPLE_BUDGETS
    object_name = "budget"

    def has_object_permission(self, request, view, obj):
        assert request.user.is_authenticated, \
            f"Permission class {self.__class__.__name__} should always be " \
            "preceeded by a permission class that guarantees authentication."
        if isinstance(obj, Template):
            return super().has_object_permission(request, view, obj)
        assert obj.created_by == request.user, \
            f"Permission class {self.__class__.__name__} should always be " \
            "preceeded by a permission class that guarantees ownership."
        if not self.user_has_products(request.user):
            return obj.is_first_created
        return True


class MultipleBudgetPermission(BaseProductPermission):
    """
    Permissions whether or not the :obj:`User` can create more than 1
    :obj:`Budget`.
    """
    message = "The user's subscription does not support multiple budgets."
    default_permission_id = ProductPermissionId.MULTIPLE_BUDGETS

    def has_permission(self, request, view):
        assert request.user.is_authenticated, \
            f"Permission class {self.__class__.__name__} should always be " \
            "preceeded by a permission class that guarantees authentication."
        if not self.user_has_products(request.user) \
                and request.method == "POST" \
                and Budget.objects.filter(created_by=request.user).count() > 0:
            return False
        return True

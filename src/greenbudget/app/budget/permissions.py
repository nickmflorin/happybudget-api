from greenbudget.app.billing import ProductPermissionId
from greenbudget.app.billing.permissions import BaseProductPermission

from .models import Budget


class BudgetProductPermission(BaseProductPermission):
    default_permission_id = ProductPermissionId.MULTIPLE_BUDGETS

    @property
    def message(self):
        access_entity_name = getattr(self, 'access_entity_name', 'budget')
        return (
            'The user does not have the correct subscription to view this %s.'
            % access_entity_name
        )

    def get_budget(self, obj):
        # Override if this permission is being used in the context of other
        # objects that related to a Budget (i.e. Accounts or SubAccounts).
        return obj

    def has_object_permission(self, request, view, obj):
        access_entity_name = getattr(self, 'access_entity_name', 'budget')
        if not self.user_has_permission(request.user):
            assert obj.created_by == request.user, \
                "Cannot check budget permissions created by user for a budget " \
                "created by another user."
            budget = self.get_budget(obj)
            if not budget.is_first_created:
                self.permission_denied(message=(
                    'The user does not have the correct subscription to '
                    'view this %s.' % access_entity_name
                ))
        return True


class MultipleBudgetPermission(BaseProductPermission):
    """
    Permissions whether or not the :obj:`User` can create more than 1
    :obj:`Budget`.
    """
    message = "The user's subscription does not support multiple budgets."
    default_permission_id = ProductPermissionId.MULTIPLE_BUDGETS

    def get_budget(self, obj):
        return obj

    def has_permission(self, request, view):
        if not self.user_has_permission(request.user):
            if request.method == "POST" \
                    and Budget.objects.filter(created_by=request.user).count() > 0:  # noqa
                self.permission_denied()
        return True

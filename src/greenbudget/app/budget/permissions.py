from greenbudget.app.billing.permissions import BaseSubscriptionPermission

from .models import Budget


def budget_is_first_created(user, obj):
    assert obj.created_by == user, \
        "Cannot check budget permissions created by user for a budget " \
        "created by another user."
    first_created = Budget.objects.filter(created_by=user).only('pk') \
        .order_by('created_at').first()
    # Since we are passing in the Budget, it should be guaranteed that there
    # exists at least one budget.
    assert first_created is not None
    return first_created.id == obj.id


class BudgetSubscriptionPermission(BaseSubscriptionPermission):

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
        if not self.user_has_permission(request.user):
            if not budget_is_first_created(request.user, self.get_budget(obj)):
                self.permission_denied()
        return True


class BudgetCountSubscriptionPermission(BaseSubscriptionPermission):
    message = (
        "The user does not have the correct subscription to create an "
        "additional budget."
    )

    def get_budget(self, obj):
        return obj

    def has_permission(self, request, view):
        if not self.user_has_permission(request.user):
            if request.method == "POST" \
                    and Budget.objects.filter(
                        created_by=request.user).count() > 0:
                self.permission_denied()
        return True

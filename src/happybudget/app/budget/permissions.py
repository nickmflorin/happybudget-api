from happybudget.lib.utils import ensure_iterable

from happybudget.app import permissions
from happybudget.app.billing import ProductPermissionId
from happybudget.app.billing.permissions import BaseProductPermission
from happybudget.app.budgeting.permissions import IsDomain
from happybudget.app.collaborator.permissions import IsCollaborator

from .models import Budget


class IsBudgetDomain(IsDomain):
    def __init__(self, *args, **kwargs):
        kwargs['domain'] = 'budget'
        super().__init__(*args, **kwargs)


class ProductPermission(BaseProductPermission):
    """
    Permissions whether or not the :obj:`User` has access to a given
    :obj:`Budget` when that :obj:`Budget` is not the first :obj:`Budget` they
    created and they are not subscribed to the correct products.
    """
    message = "The user's subscription does not support multiple budgets."
    default_permission_id = ProductPermissionId.MULTIPLE_BUDGETS
    default_object_name = "budget"

    def __init__(self, *args, **kwargs):
        self.object_name = kwargs.pop('object_name', self.default_object_name)
        super().__init__(*args, **kwargs)

    def has_object_permission(self, request, view, obj):
        assert isinstance(obj, Budget), \
            f"Permission class {self.__class__.__name__} is only applicable " \
            "for Budget related models."
        assert hasattr(obj, 'user_owner'), \
            f"Permission class {self.__class__.__name__} should always be " \
            "used for models that dictate ownership."
        assert obj.user_owner == request.user, \
            f"Permission class {self.__class__.__name__} should always be " \
            "preceeded by a permission class that guarantees ownership."
        if not self.user_has_products(request.user):
            return obj.is_first_created
        return True


class MultipleBudgetPermission(ProductPermission):
    """
    Permissions whether or not the :obj:`User` can create more than 1
    :obj:`Budget` based on whether or not they are subscribed to the correct
    products.
    """
    user_dependency_flags = ['is_authenticated', 'is_active', 'is_verified']

    def has_permission(self, request, view):
        if not self.user_has_products(request.user) \
                and Budget.objects.filter(created_by=request.user).count() > 0:
            return False
        return True


class BudgetObjPermission(permissions.OR):
    """
    Dictates whether or not the logged in :obj:`User` is allowed access to
    a :obj:`Budget` or any of it's related entities, based on the :obj:`Budget`
    that those related models are related to or the :obj:`Budget` itself.

    The governance of this permission is determined based on the following
    considerations:

    (1) User Authentication
    (2) Budget or Related Model Ownership
    (3) Budget Product Permissions
    (4) Collaboration on Budget or Related Models
    (5) Public or View Only Access to Budget or Related Models
    """
    def __init__(self, **kwargs):
        public = kwargs.pop('public', False)
        object_name = kwargs.pop('object_name', 'budget')

        # When the permission is permissioning an object that is related to
        # the Budget, we must define how to obtain the original Budget based
        # on the related object.
        get_budget = kwargs.pop('get_budget', None)

        # If the access types are not provided, it will default based on whether
        # or not the request is a SAFE request.
        access_types = kwargs.pop('collaborator_access_types', None)

        # Usually, if the User does not have the proper subscription to allow
        # access to multiple Budget(s), the User should not be able to destroy
        # entities related to the Budget.  This is not always the case though.
        # For example, the User should still be able to delete a Budget even if
        # they do not have the proper subscription to edit and view it's
        # contents.
        product_can_destroy = kwargs.pop('product_can_destroy', False)

        base_permissions = [
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                permissions.IsOwner(
                    object_name=object_name,
                    affects_after=True
                ),
                ProductPermission(
                    get_permissioned_obj=get_budget,
                    object_name=object_name,
                    is_object_applicable=lambda c:
                    c.view.action != 'destroy' or not product_can_destroy
                )
            )
        ]
        # There are some cases where we cannot allow collaborator permissions
        # on an object related to the Budget.  Right now, this is mostly
        # applicable for uploading attachments for entities that belong to
        # another User.
        collaborator = kwargs.pop('collaborator', True)
        if collaborator:
            # When collaborating on a Budget, you are allowed to delete the
            # entities of a Budget but not the Budget itself.  There may also be
            # other actions that a collaborator cannot perform on a Budget.
            collaborator_can_destroy = kwargs.pop(
                'collaborator_can_destroy', False)
            restricted_c_actions = ensure_iterable(kwargs.pop(
                'restricted_collaborator_actions', ()), cast=tuple)
            collaborator_permissions = (
                permissions.IsFullyAuthenticated(affects_after=True),
                IsCollaborator(
                    get_permissioned_obj=get_budget,
                    access_types=access_types
                )
            )
            if not collaborator_can_destroy \
                    and 'destroy' not in restricted_c_actions:
                restricted_c_actions += ('destroy', )
            if restricted_c_actions:
                collaborator_permissions = collaborator_permissions + (
                    permissions.IsNotViewAction(*restricted_c_actions), )
            base_permissions += [permissions.AND(*collaborator_permissions)]
        else:
            # These checks are simply performed to prevent unintended bugs.
            for param in [
                'collaborator_can_destroy',
                'restricted_collaborator_actions'
            ]:
                assert param not in kwargs, \
                    f"Parameter {param} is not applicable when " \
                    "the permission is not configured for collaboration."
        if public:
            base_permissions += [permissions.AND(
                permissions.IsSafeRequestMethod,
                permissions.IsPublic(get_permissioned_obj=get_budget)
            )]
        super().__init__(*base_permissions, **kwargs)

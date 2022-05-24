from django.conf import settings
from django.db import IntegrityError

from happybudget.lib.utils import get_attribute
from happybudget.app import exceptions, permissions


class ModelOwnershipMixin:
    user_ownership_field = None

    class Meta:
        abstract = True

    def has_same_owner(self, obj, raise_exception=False):
        assert type(obj) is not type(self), \
            "Ownership comparison is only meant to be performed on instances " \
            "of different classes."
        assert hasattr(obj, 'user_owner'), \
            f"The instance associated with the {obj.__class__} field must " \
            "dictate ownership."
        result = self.is_owned_by(obj.user_owner)
        if not result and raise_exception:
            raise IntegrityError(
                f"Instance {obj.pk} of model {obj.__class__.__name__} does not "
                f"have the same ownership as instance {self.pk} of model "
                f"{self.__class__.__name__}."
            )
        return result

    def is_owned_by(self, user, raise_exception=False):
        result = self.user_owner == user
        if not result and raise_exception:
            raise IntegrityError(
                f"Instance {self.pk} of model {self.__class__.__name__} does "
                f"not have the correct owner: {user.pk}."
            )
        return result

    @property
    def user_owner(self):
        # pylint: disable=import-outside-toplevel
        from .models import User
        assert self.user_ownership_field is not None, \
            f"The model {self.__class__} does not define a means of making " \
            "ownership determination."
        owner = get_attribute(self.user_ownership_field, self, delimiter='__')
        assert owner is not None and isinstance(owner, User), \
            f"The model {self.__class__} has an invalid owner {owner}."
        return owner

    @property
    def owner_is_staff(self):
        return self.user_owner.is_staff


class UserAuthenticationMixin:
    @property
    def is_fully_authenticated(self):
        return self.can_authenticate(raise_exception=False)

    def has_permissions(self, **kwargs):
        """
        A method to evaluate a set of permissions that extend
        :obj:`UserPermission` for a given :obj:`User`.
        """
        pms = kwargs.pop(
            'permissions',
            settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']
        )
        default_exception_class = kwargs.pop(
            'default_exception_class', exceptions.PermissionErr)
        raise_exception = kwargs.pop('raise_exception', True)
        hard_raise = kwargs.pop('hard_raise', False)

        for permission in permissions.instantiate_permissions(pms):
            assert hasattr(permission, 'has_user_perm'), \
                f"The permission class {permission.__class__} does not have a " \
                "user permission method."
            try:
                has_permission = permission.has_user_perm(
                    self,
                    raise_exception=True,
                    hard_raise=hard_raise
                )
            except (
                exceptions.PermissionErr,
                exceptions.NotAuthenticatedError
            ) as e:
                if raise_exception:
                    raise e
                return False
            if not has_permission:
                if raise_exception:
                    raise default_exception_class(
                        detail=getattr(permission, 'message', None),
                        hard_raise=hard_raise
                    )
                return False
        return True

    def can_authenticate(self, **kwargs):
        return self.has_permissions(
            default_exception_class=exceptions.NotAuthenticatedError,
            permissions=settings.AUTHENTICATION_PERMISSION_CLASSES,
            **kwargs
        )

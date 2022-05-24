from django.db import IntegrityError

from happybudget.lib.utils import get_attribute


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

    def has_permissions(self, permissions, **kwargs):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.permissions import check_user_permissions
        check_user_permissions(self, permissions=permissions)

    def can_authenticate(self, **kwargs):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.permissions import check_user_auth_permissions
        return check_user_auth_permissions(self, **kwargs)

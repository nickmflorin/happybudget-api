class UserAuthenticationMixin:
    @property
    def is_fully_authenticated(self):
        return self.can_authenticate(raise_exception=False)

    def has_permissions(self, permissions, raise_exception=True):
        # pylint: disable=import-outside-toplevel
        from greenbudget.app.permissions import check_user_permissions, PErrors
        try:
            check_user_permissions(
                self, permissions=permissions, raise_exception=True)
        except PErrors as e:
            if raise_exception:
                raise e
            return False
        return True

    def can_authenticate(self, raise_exception=True):
        # pylint: disable=import-outside-toplevel
        from greenbudget.app.permissions import (
            check_user_auth_permissions, PErrors)
        try:
            check_user_auth_permissions(self, raise_exception=True)
        except PErrors as e:
            if raise_exception:
                raise e
            return False
        return True

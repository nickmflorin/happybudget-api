from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models


class UserQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(is_active=True)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(is_active=False)


class UserQuery(UserQuerier, models.query.QuerySet):
    pass


class UserManager(UserQuerier, DjangoUserManager):
    queryset_class = UserQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

    def create(self, email, password=None, **kwargs):
        kwargs['username'] = email
        user = super().create(email=email, **kwargs)
        if password is not None:
            user.set_password(password)
            user.save()
        return user

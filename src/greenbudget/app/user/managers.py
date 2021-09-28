from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models

from .exceptions import InvalidSocialToken
from .utils import get_google_user_from_token


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
    use_in_migrations = True
    queryset_class = UserQuery

    def get_queryset(self):
        return self.queryset_class(self.model)

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is a required user field.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password is not None:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create(self, email, **kwargs):
        return self.create_user(email, **kwargs)

    def create_user(self, email, **kwargs):
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        kwargs.setdefault('is_admin', False)
        kwargs.setdefault('is_active', True)
        return self._create_user(email, **kwargs)

    def create_superuser(self, email, **kwargs):
        kwargs.update(is_staff=True, is_superuser=True)
        return self._create_user(email, **kwargs)

    def get_from_google_token(self, token):
        try:
            google_user = get_google_user_from_token(token)
        except InvalidSocialToken:
            raise self.model.DoesNotExist()
        else:
            user = self.get(email=google_user.email)
            user.sync_with_social_provider(social_user=google_user)
            return user

    def create_from_google_token(self, token):
        google_user = get_google_user_from_token(token)
        return self.create(
            email=google_user.email,
            first_name=google_user.first_name,
            last_name=google_user.last_name
        )

    def get_or_create_from_google_token(self, token):
        try:
            return self.get_from_google_token(token)
        except self.model.DoesNotExist:
            return self.create_from_google_token(token)

    def get_from_social_token(self, token, provider):
        assert provider == "google", "Provider %s not supported." % provider
        return self.get_from_google_token(token)

    def create_from_social_token(self, token, provider):
        assert provider == "google", "Provider %s not supported." % provider
        return self.create_from_google_token(token)

    def get_or_create_from_social_token(self, token, provider):
        assert provider == "google", "Provider %s not supported." % provider
        return self.get_or_create_from_google_token(token)

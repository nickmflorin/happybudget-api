import logging

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import IntegrityError

from happybudget.conf import suppress_with_setting

from happybudget.app.authentication.exceptions import (
    InvalidSocialToken, AccountNotOnWaitlist)

from .mail import user_is_on_waitlist
from .query import UserQuerySet, UserQuerier


logger = logging.getLogger('happybudget')


class UserManager(UserQuerier, DjangoUserManager):
    use_in_migrations = True
    queryset_class = UserQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model)

    def _create_user(self, email, password, **kwargs):
        force = kwargs.pop('force', False)
        kwargs.setdefault('has_password', True)
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        kwargs.setdefault('is_active', True)

        if settings.WAITLIST_ENABLED is True and force is not True \
                and kwargs['is_staff'] is False \
                and kwargs['is_superuser'] is False \
                and not user_is_on_waitlist(email):
            raise AccountNotOnWaitlist()

        if kwargs['is_superuser'] is True or kwargs['is_staff'] is True:
            kwargs['is_verified'] = True

        email = self.normalize_email(email)
        if kwargs['has_password'] and password in (None, ""):
            raise IntegrityError("The password must be a non-empty string.")
        elif not kwargs['has_password'] and password != "":
            raise IntegrityError("The password must be an empty string.")

        user = self.model(email=email, **kwargs)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create(self, email, password, **kwargs):
        return self._create_user(email, password, **kwargs)

    @suppress_with_setting("SOCIAL_AUTHENTICATION_ENABLED", exc=True)
    def create_from_social(self, email, **kwargs):
        kwargs.update(password="", has_password=False, is_verified=True)
        return self._create_user(email, **kwargs)

    def create_superuser(self, email, password, **kwargs):
        kwargs.update(is_staff=True, is_superuser=True, is_verified=True)
        return self._create_user(email, password, **kwargs)

    @suppress_with_setting("SOCIAL_AUTHENTICATION_ENABLED", exc=True)
    def get_from_social_token(self, token_id, provider):
        try:
            social_user = self.model.get_social_user(token_id, provider)
        except InvalidSocialToken as e:
            raise self.model.DoesNotExist() from e
        else:
            user = self.get(email=social_user.email)
            user.sync_with_social_provider(social_user=social_user)
            user.save()
            return user

    @suppress_with_setting("SOCIAL_AUTHENTICATION_ENABLED", exc=True)
    def create_from_social_token(self, token_id, provider):
        social_user = self.model.get_social_user(token_id, provider)
        return self.create_from_social(
            email=social_user.email,
            first_name=social_user.first_name,
            last_name=social_user.last_name
        )

    @suppress_with_setting("SOCIAL_AUTHENTICATION_ENABLED", exc=True)
    def get_or_create_from_social_token(self, token_id, provider):
        try:
            user = self.get_from_social_token(token_id, provider)
        except self.model.DoesNotExist:
            return self.create_from_social_token(token_id, provider)
        else:
            # If a user is created as a result of social authentication, then
            # there email should already be considered verified because,
            # at least currently, authenticating via social authentication
            # inherently means the email address belongs to the user.
            if not user.is_verified:
                user.is_verified = True
                user.save(update_fields=['is_verified'])
            return user

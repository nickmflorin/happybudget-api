import logging
import requests

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import IntegrityError

from greenbudget.lib.utils.urls import add_query_params_to_url

from greenbudget.app.authentication.exceptions import (
    InvalidSocialProvider, InvalidSocialToken, AccountNotOnWaitlist)

from .mail import user_is_on_waitlist
from .query import UserQuerySet, UserQuerier


logger = logging.getLogger('greenbudget')


def get_social_google_user(token):
    # pylint: disable=import-outside-toplevel
    from .models import SocialUser
    url = add_query_params_to_url(
        settings.GOOGLE_OAUTH_API_URL, id_token=token)
    try:
        response = requests.get(url)
    except requests.RequestException as e:
        logger.error("Network Error Validating Google Token: %s" % e)
        raise InvalidSocialToken() from e
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP Error Validating Google Token: %s" % e)
            raise InvalidSocialToken() from e
        else:
            data = response.json()
            return SocialUser(
                first_name=data['given_name'],
                last_name=data['family_name'],
                email=data['email']
            )


SOCIAL_USER_LOOKUPS = {
    'google': get_social_google_user
}


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

    def create_from_social(self, email, **kwargs):
        kwargs.update(password="", has_password=False, is_verified=True)
        return self._create_user(email, **kwargs)

    def create_superuser(self, email, password, **kwargs):
        kwargs.update(is_staff=True, is_superuser=True, is_verified=True)
        return self._create_user(email, password, **kwargs)

    def get_social_user(self, token, provider):
        try:
            return SOCIAL_USER_LOOKUPS[provider](token)
        except KeyError as e:
            raise InvalidSocialProvider() from e

    def get_from_google_token(self, token_id):
        try:
            google_user = self.get_social_user(token_id, "google")
        except InvalidSocialToken as e:
            raise self.model.DoesNotExist() from e
        else:
            user = self.get(email=google_user.email)
            user.sync_with_social_provider(social_user=google_user)
            user.save()
            return user

    def create_from_google_token(self, token_id):
        google_user = self.get_social_user(token_id, "google")
        return self.create_from_social(
            email=google_user.email,
            first_name=google_user.first_name,
            last_name=google_user.last_name
        )

    def get_or_create_from_google_token(self, token_id):
        try:
            user = self.get_from_google_token(token_id)
        except self.model.DoesNotExist:
            return self.create_from_google_token(token_id)
        else:
            if not user.is_verified:
                user.is_verified = True
                user.save(update_fields=['is_verified'])
            return user

    def get_from_social_token(self, token_id, provider):
        assert provider == "google", "Provider %s not supported." % provider
        return self.get_from_google_token(token_id)

    def create_from_social_token(self, token_id, provider):
        assert provider == "google", "Provider %s not supported." % provider
        return self.create_from_google_token(token_id)

    def get_or_create_from_social_token(self, token_id, provider):
        assert provider == "google", "Provider %s not supported." % provider
        return self.get_or_create_from_google_token(token_id)

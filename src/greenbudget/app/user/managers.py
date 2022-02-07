import logging
import requests

from django.conf import settings
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models

from greenbudget.lib.utils.urls import add_query_params_to_url

from greenbudget.app.authentication.exceptions import (
    InvalidSocialProvider, InvalidSocialToken)


logger = logging.getLogger('greenbudget')


def get_social_google_user(token):
    from .models import SocialUser
    url = add_query_params_to_url(
        settings.GOOGLE_OAUTH_API_URL, id_token=token)
    try:
        response = requests.get(url)
    except requests.RequestException as e:
        logger.error("Network Error Validating Google Token: %s" % e)
        raise InvalidSocialToken()
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP Error Validating Google Token: %s" % e)
            raise InvalidSocialToken()
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


class UserQuerier(object):

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
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
        email = self.normalize_email(email).lower()
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
        kwargs.setdefault('is_active', True)
        return self._create_user(email, **kwargs)

    def create_superuser(self, email, **kwargs):
        kwargs.update(is_staff=True, is_superuser=True, is_verified=True)
        return self._create_user(email, **kwargs)

    def get_social_user(self, token, provider):
        try:
            return SOCIAL_USER_LOOKUPS[provider](token)
        except KeyError:
            raise InvalidSocialProvider()

    def get_from_google_token(self, token_id):
        try:
            google_user = self.get_social_user(token_id, "google")
        except InvalidSocialToken:
            raise self.model.DoesNotExist()
        else:
            user = self.get(email=google_user.email)
            user.sync_with_social_provider(social_user=google_user)
            user.save()
            return user

    def create_from_google_token(self, token_id):
        google_user = self.get_social_user(token_id, "google")
        return self.create(
            email=google_user.email,
            is_verified=True,
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

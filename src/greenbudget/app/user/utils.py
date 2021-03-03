import collections
import logging
import requests

from django.conf import settings

from greenbudget.lib.utils.urls import add_query_params_to_url

from .exceptions import InvalidSocialToken, InvalidSocialProvider


logger = logging.getLogger('greenbudget')


SocialUser = collections.namedtuple(
    'SocialUser', ['first_name', 'last_name', 'email'])


def get_google_user_from_token(token):
    url = add_query_params_to_url(settings.GOOGLE_OAUTH_API_URL, id_token=token)
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


def get_user_from_social_token(token, provider):
    if provider != "google":
        raise InvalidSocialProvider()
    return get_google_user_from_token(token)

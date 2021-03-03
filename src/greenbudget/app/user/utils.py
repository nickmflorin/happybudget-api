import collections
import logging
import requests

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

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


def send_forgot_password_email(user, token):
    """
    Sends a reset password email to the provided user with the token embedded
    in the email.

    Parameters:
    ----------
    user: :obj:`backend.app.user.models.CustomUser`
        The user who submitted the password reset request.
    token: :obj:`str`
        The randomly generated token that will be used to verify the password
        recovery.
    """
    html_message = render_to_string('email/forgot_password.html', {
        'PWD_RESET_LINK': add_query_params_to_url(
            settings.RESET_PWD_UI_LINK, token=token),
        'from_email': settings.FROM_EMAIL,
        'EMAIL': user.email,
        'year': timezone.now().year,
        'NAME': "{0} {1}".format(user.first_name, user.last_name),
    })
    mail = EmailMultiAlternatives(
        "Forgot Password",
        strip_tags(html_message),
        settings.FROM_EMAIL,
        [user.email]
    )
    mail.attach_alternative(html_message, "text/html")

    if settings.EMAIL_ENABLED:
        mail.send()

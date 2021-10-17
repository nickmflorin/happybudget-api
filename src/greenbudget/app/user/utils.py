from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from greenbudget.lib.django_utils.storages import get_image_filename
from greenbudget.lib.utils.urls import add_query_params_to_url


def user_image_directory(user):
    return f'users/{user.pk}'


def user_image_temp_directory(user):
    return f'{user_image_directory(user)}/temp'


def upload_temp_user_image_to(user, filename, directory=None, new_filename=None):  # noqa
    filename = get_image_filename(filename, new_filename=new_filename)
    if directory is not None:
        return f'{user_image_temp_directory(user)}/{directory}/{filename}'
    return f'{user_image_temp_directory(user)}/{filename}'


def upload_user_image_to(user, filename, directory=None, new_filename=None):
    filename = get_image_filename(filename, new_filename=new_filename)
    if directory is not None:
        return f'{user_image_directory(user)}/{directory}/{filename}'
    return f'{user_image_directory(user)}/{filename}'


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

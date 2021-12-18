import json
import logging
import requests
import os

from django.conf import settings

from python_http_client import exceptions
import sendgrid
from sendgrid.helpers.mail import Mail as SendGridMail

from greenbudget.conf import suppress_with_setting
from greenbudget.lib.utils.urls import add_query_params_to_url

from greenbudget.app.authentication.exceptions import EmailError
from greenbudget.app.authentication.tokens import AccessToken


logger = logging.getLogger("greenbudget")


api_client = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)


def user_is_on_waitlist(email):
    try:
        response = requests.post(
            os.path.join(
                settings.SENDGRID_API_URL, "marketing/contacts/search/emails"),
            headers={
                'Authorization': f'Bearer {settings.SENDGRID_API_KEY}',
                'Accept': 'application/json',
                'Access-Control-Allow-Methods': (
                    'OPTIONS, GET, POST, PUT, PATCH, DELETE, HEAD, LINK, UNLINK')  # noqa
            },
            data=json.dumps({'emails': [email]})
        )
    except requests.exceptions.RequestException as e:
        logger.error(
            "There was a request error checking the waitlist for user %s: \n%s"
            % (email, e)
        )
        return False
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # SendGrid will return a 404 if the user's provided email address
            # is not in the searched contacts.
            if response.status_code != 404:
                logger.error(
                    "There was an http error checking the waitlist for "
                    "user %s: \n%s" % (email, e)
                )
            return False
        data = response.json()
        return email in data['result']


def get_template(slug):
    try:
        return [
            t for t in settings.SENDGRID_TEMPLATES
            if t.slug == slug
        ][0]
    except IndexError:
        raise LookupError("Template %s is not configured in settings." % slug)


class Mail(SendGridMail):
    def __init__(self, user, **kwargs):
        redirect_query = kwargs.pop('redirect_query', None)
        super().__init__(
            to_emails=user.email,
            from_email=settings.FROM_EMAIL,
            **kwargs
        )
        self.user = user
        self.template_id = self.template_obj.id

        # Redirect Base URL is a LazySetting
        redirect_url = str(self.template_obj.redirect_base_url)
        if redirect_query is not None:
            redirect_url = add_query_params_to_url(
                redirect_url, **redirect_query)

        self.dynamic_template_data = {'url': redirect_url}

    @property
    def template_obj(self):
        return get_template(self.template_slug)

    @property
    def template_slug(self):
        raise NotImplementedError()


class PostActivationMail(Mail):
    template_slug = "post_activation"


class EmailConfirmationMail(Mail):
    template_slug = "email_confirmation"

    def __init__(self, user, token, **kwargs):
        super().__init__(
            user=user,
            redirect_query={"token": token},
            **kwargs
        )


class PasswordRecoveryMail(Mail):
    template_slug = "password_recovery"

    def __init__(self, user, token, **kwargs):
        super().__init__(
            user=user,
            redirect_query={"token": token},
            **kwargs
        )


def parse_errors_from_request(e):
    body = getattr(e, "body", None)
    try:
        body = json.loads(body, )
    except TypeError:
        return None
    if isinstance(body, dict) and body.get("errors") is not None:
        error_messages = []
        for error in body["errors"]:
            if not isinstance(error, dict) or error.get("message") is None:
                logger.warning(
                    "Could not parse error message from SendGrid error: \n%s"
                    % error
                )
            else:
                error_messages.append(error["message"])
        return error_messages
    return None


def format_errors_from_request(e):
    error_messages = parse_errors_from_request(e)
    if error_messages is not None:
        return "\n".join([
            "(%s) %s" % (i + 1, msg) for i, msg in enumerate(error_messages)
        ])
    return None


@suppress_with_setting("EMAIL_ENABLED")
def send_mail(mail):
    try:
        return api_client.client.mail.send.post(request_body=mail.get())
    except (exceptions.BadRequestsError, exceptions.ForbiddenError,
            exceptions.UnauthorizedError) as e:
        parsed_messages = format_errors_from_request(e)
        if parsed_messages is not None:
            logger.error(
                "There were error(s) sending the email: \n%s"
                % parsed_messages
            )
        else:
            logger.error("There was an error sending email: \n%s" % str(e))
        raise EmailError()


def send_email_verification_email(user, token=None):
    token = token or AccessToken.for_user(user)
    mail = EmailConfirmationMail(user, str(token))
    return send_mail(mail)


def send_password_recovery_email(user, token=None):
    token = token or AccessToken.for_user(user)
    mail = PasswordRecoveryMail(user, str(token))
    return send_mail(mail)


def send_post_activation_email(user):
    mail = PostActivationMail(user)
    return send_mail(mail)

import json
import logging

from django.conf import settings

from python_http_client import exceptions
import sendgrid
from sendgrid.helpers.mail import Mail as SendGridMail

from greenbudget.conf import suppress_with_setting
from greenbudget.lib.utils.urls import add_query_params_to_url

from .exceptions import EmailError
from .tokens import AccessToken


logger = logging.getLogger("greenbudget")


api_client = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)


class Mail(SendGridMail):
    def __init__(self, user, data, **kwargs):
        super().__init__(
            to_emails=user.email,
            from_email=settings.FROM_EMAIL,
            **kwargs
        )
        self.user = user
        self.template_id = kwargs.pop(
            'template_id', getattr(self, 'template'))
        self.dynamic_template_data = data


class EmailVerification(Mail):
    template = settings.EMAIL_VERIFICATION_TEMPLATE_ID

    def __init__(self, user, token, **kwargs):
        super().__init__(
            user=user,
            data={'redirect_url': add_query_params_to_url(
                settings.FRONTEND_EMAIL_CONFIRM_URL,
                token=token
            )},
            **kwargs
        )


class PasswordRecovery(Mail):
    template = settings.PASSWORD_RECOVERY_TEMPLATE_ID

    def __init__(self, user, token, **kwargs):
        super().__init__(
            user=user,
            data={'redirect_url': add_query_params_to_url(
                settings.FRONTEND_PASSWORD_RECOVERY_URL,
                token=token
            )},
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
                logger.warn(
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
    mail = EmailVerification(user, str(token))
    return send_mail(mail)


def send_password_recovery_email(user, token=None):
    token = token or AccessToken.for_user(user)
    mail = PasswordRecovery(user, str(token))
    return send_mail(mail)

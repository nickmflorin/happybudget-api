import logging

from django.conf import settings

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from greenbudget.conf import suppress_with_setting
from greenbudget.lib.utils.urls import add_query_params_to_url

from greenbudget.app.authentication.exceptions import EmailError
from greenbudget.app.authentication.tokens import AccessToken


logger = logging.getLogger("greenbudget")


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.SEND_IN_BLUE_API_KEY

client = sib_api_v3_sdk.ApiClient(configuration)
contacts_api = sib_api_v3_sdk.ContactsApi(client)

email_api = sib_api_v3_sdk.TransactionalEmailsApi(client)


def user_is_on_waitlist(email):
    try:
        response = contacts_api.get_contacts_from_list(
            settings.SEND_IN_BLUE_WHITELIST_ID)
    except ApiException as e:
        logger.error(
            "There was a request error checking the waitlist for user %s: \n%s"
            % (email, e)
        )
        return False
    else:
        return email in [
            c["email"] for c in response.contacts
            if c["emailBlacklisted"] is not True
        ]


def get_template(slug):
    try:
        return [
            t for t in settings.SEND_IN_BLUE_TEMPLATES
            if t.slug == slug
        ][0]
    except IndexError:
        raise LookupError("Template %s is not configured in settings." % slug)


class Mail(sib_api_v3_sdk.SendSmtpEmail):
    def __init__(self, user, redirect_query=None):
        # Redirect Base URL is a LazySetting
        redirect_url = str(self.template_obj.redirect_base_url)
        if redirect_query is not None:
            redirect_url = add_query_params_to_url(
                redirect_url, **redirect_query)
        super().__init__(
            to=[{"email": user.email}],
            template_id=self.template_obj.id,
            params={"redirect_url": redirect_url}
        )

    @property
    def template_obj(self):
        return get_template(self.template_slug)

    @property
    def template_slug(self):
        raise NotImplementedError()


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


@suppress_with_setting("EMAIL_ENABLED")
def send_mail(mail):
    try:
        email_api.send_transac_email(mail)
    except ApiException as e:
        logger.error("There was an error sending email: \n%s" % str(e))
        raise EmailError()


def send_email_confirmation_email(user, token=None):
    token = token or AccessToken.for_user(user)
    mail = EmailConfirmationMail(user, str(token))
    return send_mail(mail)


def send_password_recovery_email(user, token=None):
    token = token or AccessToken.for_user(user)
    mail = PasswordRecoveryMail(user, str(token))
    return send_mail(mail)

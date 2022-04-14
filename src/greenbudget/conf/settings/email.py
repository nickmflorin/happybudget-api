import collections
import os

from greenbudget.conf import config, Environments, LazySetting

SendInBlueTemplate = collections.namedtuple("SendInBlueTemplate", [
    "id",
    "redirect_base_url",
    "slug"
])

EMAIL_ENABLED = True
FROM_EMAIL = "noreply@greenbudget.io"
EMAIL_HOST = 'smtp.sendgrid.net'

SEND_IN_BLUE_WHITELIST_ID = 11

SEND_IN_BLUE_API_KEY = config(
    name='SEND_IN_BLUE_API_KEY',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
)

SEND_IN_BLUE_TEMPLATES = [
    SendInBlueTemplate(
        id=2,
        slug="password_recovery",
        redirect_base_url=LazySetting(
            lambda settings: os.path.join(
                str(settings.FRONTEND_URL), "recovery")
        )
    ),
    SendInBlueTemplate(
        id=1,
        slug="email_verification",
        redirect_base_url=LazySetting(
            lambda settings: os.path.join(
                str(settings.FRONTEND_URL), "verify")
        )
    )
]

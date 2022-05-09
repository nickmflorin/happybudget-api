import collections
import os

from happybudget.conf import config, Environments, LazySetting

SendInBlueTemplate = collections.namedtuple("SendInBlueTemplate", [
    "id",
    "redirect_base_url",
    "slug"
])

EMAIL_ENABLED = False  # Post Copyright Infringement
FROM_EMAIL = "noreply@happybudget.io"  # Post Copyright Infringement
EMAIL_HOST = 'smtp.sendgrid.net'  # Post Copyright Infringement

# Post Copyright Infringement - All Configurations
SEND_IN_BLUE_WHITELIST_ID = 11

SEND_IN_BLUE_API_KEY = config(
    name='SEND_IN_BLUE_API_KEY',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    enabled=EMAIL_ENABLED
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

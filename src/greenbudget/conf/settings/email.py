import collections
import os

from greenbudget.conf import config, Environments, LazySetting

SendGridTemplate = collections.namedtuple("SendGridTemplate", [
    "id",
    "redirect_base_url",
    "slug"
])

EMAIL_ENABLED = True
FROM_EMAIL = "noreply@greenbudget.io"
EMAIL_HOST = 'smtp.sendgrid.net'

SENDGRID_API_URL = "https://api.sendgrid.com/v3/"
SENDGRID_API_KEY = config(
    name='SENDGRID_API_KEY',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
)

SENDGRID_TEMPLATES = [
    SendGridTemplate(
        id="d-577a2dda8c2d4e3dabff2337240edf79",
        slug="password_recovery",
        redirect_base_url=LazySetting(
            lambda settings: os.path.join(
                str(settings.FRONTEND_URL), "recovery")
        )
    ),
    SendGridTemplate(
        id="d-3f3c585c80514e46809b9d3a46134674",
        slug="email_confirmation",
        redirect_base_url=LazySetting(
            lambda settings: os.path.join(
                str(settings.FRONTEND_URL), "verify")
        )
    )
]

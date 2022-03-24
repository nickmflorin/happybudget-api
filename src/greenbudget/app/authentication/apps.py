from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    name = 'greenbudget.app.authentication'
    verbose_name = "Authentication"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import greenbudget.app.authentication.signals  # noqa

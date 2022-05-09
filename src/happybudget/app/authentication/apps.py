from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    name = 'happybudget.app.authentication'
    verbose_name = "Authentication"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import happybudget.app.authentication.signals  # noqa

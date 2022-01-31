from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    name = 'greenbudget.app.authentication'
    verbose_name = "Authentication"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import greenbudget.app.authentication.signals  # noqa

from django.apps import AppConfig


class IOConfig(AppConfig):
    name = 'greenbudget.app.io'
    verbose_name = "IO"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import greenbudget.app.io.signals  # noqa

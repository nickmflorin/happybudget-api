from django.apps import AppConfig


class IOConfig(AppConfig):
    name = 'greenbudget.app.io'
    verbose_name = "IO"

    def ready(self):
        import greenbudget.app.io.signals  # noqa

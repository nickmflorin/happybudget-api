from django.apps import AppConfig


class ActualConfig(AppConfig):
    name = 'greenbudget.app.actual'
    verbose_name = "Actual"

    def ready(self):
        import greenbudget.app.actual.signals  # noqa

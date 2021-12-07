from django.apps import AppConfig


class ActualConfig(AppConfig):
    name = 'greenbudget.app.actual'
    verbose_name = "Actual"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import greenbudget.app.actual.signals  # noqa

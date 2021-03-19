from django.apps import AppConfig


class HistoryConfig(AppConfig):
    name = 'greenbudget.app.history'
    verbose_name = "History"

    def ready(self):
        import greenbudget.app.history.signals  # noqa

from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'greenbudget.app.common'
    verbose_name = "Common"

    def ready(self):
        import greenbudget.app.common.signals  # noqa

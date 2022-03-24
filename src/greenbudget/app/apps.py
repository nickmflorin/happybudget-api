from django.apps import AppConfig


class GreenbudgetAppConfig(AppConfig):
    name = 'greenbudget.app'
    verbose_name = "Greenbudget App"

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import greenbudget.app.signals.receivers  # noqa

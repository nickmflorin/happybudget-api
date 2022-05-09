from django.apps import AppConfig


class GreenbudgetAppConfig(AppConfig):
    name = 'greenbudget.app'
    verbose_name = "Greenbudget App"

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        from .signals import receivers  # noqa

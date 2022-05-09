from django.apps import AppConfig


class HappyBudgetAppConfig(AppConfig):
    name = 'happybudget.app'
    verbose_name = "HappyBudget App"

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        from .signals import receivers  # noqa

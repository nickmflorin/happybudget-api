from django.apps import AppConfig


class GreenbudgetAppConfig(AppConfig):
    name = 'happybudget.app'
    verbose_name = "HappyBudget App"

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import happybudget.app.signals.receivers  # noqa

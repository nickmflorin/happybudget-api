from django.apps import AppConfig


class SubAccountConfig(AppConfig):
    name = 'greenbudget.app.subaccount'
    verbose_name = "SubAccount"

    def ready(self):
        import greenbudget.app.subaccount.signals  # noqa

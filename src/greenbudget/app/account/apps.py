from django.apps import AppConfig


class AccountConfig(AppConfig):
    name = 'greenbudget.app.account'
    verbose_name = "Account"

    def ready(self):
        import greenbudget.app.account.signals  # noqa

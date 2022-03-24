from django.apps import AppConfig


class AccountConfig(AppConfig):
    name = 'greenbudget.app.account'
    verbose_name = "Account"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import greenbudget.app.account.signals  # noqa

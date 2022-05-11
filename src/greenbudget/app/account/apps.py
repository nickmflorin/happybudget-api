from django.apps import AppConfig


class AccountConfig(AppConfig):
    name = 'happybudget.app.account'
    verbose_name = "Account"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import happybudget.app.account.signals  # noqa

from django.apps import AppConfig


class SubAccountConfig(AppConfig):
    name = 'happybudget.app.subaccount'
    verbose_name = "SubAccount"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import happybudget.app.subaccount.signals  # noqa

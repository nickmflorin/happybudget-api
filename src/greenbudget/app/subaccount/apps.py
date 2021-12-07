from django.apps import AppConfig


class SubAccountConfig(AppConfig):
    name = 'greenbudget.app.subaccount'
    verbose_name = "SubAccount"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import greenbudget.app.subaccount.signals  # noqa

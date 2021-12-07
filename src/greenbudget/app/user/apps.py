from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'greenbudget.app.user'
    verbose_name = "User"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import greenbudget.app.user.signals  # noqa

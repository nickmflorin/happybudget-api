from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'greenbudget.app.user'
    verbose_name = "User"

    def ready(self):
        import greenbudget.app.user.signals  # noqa

from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'greenbudget.app.user'
    verbose_name = "User"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # pylint: disable=import-outside-toplevel, unused-import
        import greenbudget.app.user.signals  # noqa

        from .contrib import AnonymousUser

        # pylint: disable=import-outside-toplevel
        import django.contrib.auth.models as django_auth_models
        django_auth_models.AnonymousUser = AnonymousUser
